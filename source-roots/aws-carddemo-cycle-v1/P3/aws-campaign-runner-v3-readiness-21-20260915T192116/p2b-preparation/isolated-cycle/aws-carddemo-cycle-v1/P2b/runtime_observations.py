"""Local runtime evidence conversion; no business-rule reconstruction."""
import re

SPANS = [('transactionId',0,16),('typeCode',16,18),('categoryCode',18,22),('source',22,32),('description',32,132),('amount',132,143),('merchantId',143,152),('merchantName',152,202),('merchantCity',202,252),('merchantPostalText',252,262),('cardReference',262,278),('originalTimestamp',278,304),('processingTimestamp',304,330)]


def transaction_fields(raw):
    if len(raw) != 350:
        raise ValueError('transaction receiver must contain 350 bytes')
    return {name: raw[start:end].decode('ascii') for name,start,end in SPANS}


def posting_observations(log, invocation, stdout):
    body = {'track':'posting', 'completeness':'not_attested', 'durability':'unknown',
            'outputs':{'availability':'unavailable'}, 'rejections':{'availability':'unavailable'}, 'progress':{'availability':'unavailable'}}
    ev = {'knownFailure':False, 'events':[], 'scope':'returned cob_write calls; not durability or business completeness', 'fieldSpans':SPANS}
    fields = [('processedRecordCount', r'^TRANSACTIONS PROCESSED :([0-9]{9})$'), ('preliminaryRejectCount', r'^TRANSACTIONS REJECTED  :([0-9]{9})$')]
    observed = {name:re.findall(pattern, stdout, re.MULTILINE) for name,pattern in fields}
    if all(len(values)==1 for values in observed.values()):
        body['progress']={'availability':'available','value':{key:int(values[0]) for key,values in observed.items()}}
    if log is None:
        return body, ev
    lines=log.splitlines()
    if not lines or lines[0] != 'BEGIN|'+invocation:
        ev['knownFailure']=True; ev['captureConflict']='missing/misattributed BEGIN'
        return body, ev
    streams={'outputs':[], 'rejections':[]}
    count=0
    complete=False
    try:
        for pos,line in enumerate(lines[1:],1):
            if line.startswith('END|'):
                if line != f'END|{invocation}|{count}' or pos != len(lines)-1:
                    raise ValueError('invalid END/count/trailing data')
                complete=True
                break
            tag,number,name,status,hexdata=line.split('|')
            count+=1
            if tag!='WRITE' or int(number)!=count:
                raise ValueError('noncontiguous observation sequence')
            raw=bytes.fromhex(hexdata)
            event={'sequence':count,'select':name,'status':status,'rawHex':hexdata}
            ev['events'].append(event)
            if status!='00':
                ev['knownFailure']=True
                continue
            if name=='TRANSACT-FILE':
                item=transaction_fields(raw)
                event['publicDestination']=['outputs',len(streams['outputs'])]
                streams['outputs'].append(item)
            elif name=='DALYREJS-FILE':
                if len(raw)!=430: raise ValueError('rejection receiver must contain 430 bytes')
                reason=raw[350:354].decode('ascii')
                if reason not in ('0100','0101','0102','0103'):
                    raise ValueError('unrepresentable preliminary rejection reason retained internally')
                candidate=transaction_fields(raw[:350])
                candidate['suppliedProcessingTimestamp']=candidate.pop('processingTimestamp')
                event['publicDestination']=['rejections',len(streams['rejections'])]
                streams['rejections'].append({'candidate':candidate,'reason':reason[1:],'description':raw[354:430].decode('ascii')})
        if not complete: raise ValueError('observation stream missing END')
    except (ValueError, UnicodeError) as exc:
        ev['knownFailure']=True; ev['captureConflict']=str(exc)
    for channel,items in streams.items():
        if items or complete:
            body[channel]={'availability':'available','items':items}
    ev['completeCaptureFrame']=complete
    return body, ev


def apply_failure_boundary(track, status, body, cmd):
    # Exact diagnostic of the local compatibility routine, not a claim that
    # exit values or source branches define CEE3ABD/mainframe semantics.
    events=[]
    for line in cmd.get('stderr','').splitlines():
        if re.fullmatch(r'LOCAL-CEE3ABD/2 CODE=[+-][0-9]+ TIMING=[+-][0-9]+', line):
            events.append({'kind':'local_compatibility_abort','raw':line,'authority':'local CEE3ABD2 compatibility diagnostic; cause/effects not inferred'})
        if line in ('P2B-PARAMETER-FAIL: open', 'P2B-PARAMETER-FAIL: read'):
            events.append({'kind':'local_parameter_transport_failure','raw':line,'authority':'P2B_INTEREST_DRIVER file transport'})
        if line.startswith('P2B-CAPTURE-FAIL:'):
            events.append({'kind':'observation_write_failure','raw':line,'authority':'local write observer'})
    if not events:
        return status, body, events
    failure={'track':track,'category':'technical_failure','completeness':'not_attested','durability':'unknown'}
    content=body.get('availableContent') if 'category' in body else body
    if content and any(isinstance(v,dict) and v.get('availability')=='available' for v in content.values()):
        failure['availableContent']=content
    return 500, failure, events
