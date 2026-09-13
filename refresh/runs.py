"""Comparable local runs and bounded replay inspection. No public trust claim."""
import math
from . import stages

RULES='refresh24-v2'
ACTIONS={'LEFT','RIGHT','UP','JUMP','DOWN'}
MAX_INPUTS=86400

def clock_text(seconds):
    milliseconds=max(0,round(seconds*1000))
    minutes,rest=divmod(milliseconds,60000)
    seconds,ms=divmod(rest,1000)
    return f'{minutes:02d}:{seconds:02d}.{ms:03d}'

def category(tempo,dialogue):
    return f'{tempo:g}x:'+('story' if dialogue else 'no-dialogue')

def record_key(document,tempo,dialogue):
    return f'{stages.fingerprint(document)}:{RULES}:{category(tempo,dialogue)}'

def replay(document,session,tempo,dialogue,pauses,finished=False):
    return dict(schema=2,stage_hash=stages.fingerprint(document),rules=RULES,tempo=tempo,
                dialogue=dialogue,seed=session.seed,inputs=session.history,
                complete=finished and not getattr(session,'history_truncated',False),
                ticks=session.score.time,pauses=pauses,category=category(tempo,dialogue))

def validate_replay(payload,document):
    if not isinstance(payload,dict) or payload.get('schema')!=2:raise ValueError('Expected replay schema 2')
    if payload.get('rules')!=RULES:raise ValueError('Unsupported rules')
    if payload.get('stage_hash')!=stages.fingerprint(document):raise ValueError('Replay belongs to different stage content')
    tempo=payload.get('tempo')
    if type(tempo) not in (int,float) or not math.isfinite(tempo) or tempo not in (.75,1.,1.25,1.5):raise ValueError('Invalid tempo')
    if type(payload.get('dialogue')) is not bool:raise ValueError('Invalid dialogue setting')
    if payload.get('category')!=category(tempo,payload['dialogue']):raise ValueError('Category mismatch')
    if type(payload.get('seed')) is not int or not 0<=payload['seed']<2**32:raise ValueError('Invalid seed')
    for field in ('ticks','pauses'):
        if type(payload.get(field)) is not int or not 0<=payload[field]<=MAX_INPUTS:raise ValueError('Invalid '+field)
    if type(payload.get('complete')) is not bool:raise ValueError('Invalid completion flag')
    inputs=payload.get('inputs')
    if not isinstance(inputs,list) or not 1<=len(inputs)<=MAX_INPUTS:raise ValueError('Replay must contain 1–86400 input frames')
    for frame in inputs:
        if not isinstance(frame,dict) or set(frame)-ACTIONS or any(type(v) is not bool for v in frame.values()):
            raise ValueError('Invalid replay input')
    return payload

def verify(payload,document,settings):
    """Local deterministic verification, to be isolated/bounded by a future server."""
    from .runtime import Session
    validate_replay(payload,document)
    session=Session(stages.materialize(document),dict(settings,sound=False,dialogue=payload['dialogue']),seed=payload['seed'])
    for index,frame in enumerate(payload['inputs']):
        if session.result is not None:raise ValueError('Inputs continue after the run ended')
        session.step(frame)
    if not payload['complete'] or session.result!=3:raise ValueError('Replay does not complete the stage')
    if session.score.time!=payload['ticks']:raise ValueError('Claimed time differs from simulated time')
    return {'verified_locally':True,'ticks':session.score.time,'seconds':session.score.time/24/payload['tempo'],
            'category':payload['category'],'stage_hash':payload['stage_hash']}
