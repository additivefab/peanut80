"""Diagnostic mapping only; no optical calibration or fabricated image filling."""
from __future__ import annotations
from dataclasses import dataclass
from bisect import bisect_right
import math
from zlraw import *
@dataclass(frozen=True)
class ScanLine:
    line_id:int
    sos_tick:int
    eos_tick:int
    relative_facet:int
    absolute_facet:int|None=None

def lines_from_records(records:list[Record],facet_count:int=6)->list[ScanLine]:
    if facet_count<1:raise ValueError('facet_count')
    # Events share a clock epoch. Global wire order need not be chronological.
    events=sorted((r for r in records if r.kind in (SOS_UP,EOS_UP)),key=lambda r:r.tick)
    pending=None;out=[];seen_ids=set()
    for r in events:
        if r.kind==SOS_UP:
            if r.payload in seen_ids: raise FormatError('duplicate line id')
            seen_ids.add(r.payload)
            if pending is not None: raise FormatError('SOS before previous EOS')
            pending=r
        elif pending is not None:
            if r.payload!=pending.payload or r.tick<=pending.tick:raise FormatError('EOS mismatch')
            out.append(ScanLine(r.payload,pending.tick,r.tick,(r.payload-1)%facet_count))
            pending=None
    # A final incomplete line is not fabricated; it is excluded and counted by the caller.
    return out

def x_mm(tick:int,line:ScanLine,sync_span_mm:float=92.,sensor_delay_ticks:float=0.)->float:
    if line.eos_tick<=line.sos_tick or sync_span_mm<=0:raise ValueError('invalid scan geometry')
    s=line.sos_tick-sensor_delay_ticks;e=line.eos_tick-sensor_delay_ticks
    return -sync_span_mm/2+sync_span_mm*(tick-s)/(e-s)

def encoder_points(records:list[Record],kind:int=ENC_M)->list[tuple[int,int]]:
    # Invalid quadrature is a hard diagnostic error, not an interpolation opportunity.
    raw=sorted((r for r in records if r.kind==kind),key=lambda r:r.tick)
    out=[]
    for r in raw:
        if r.flags&4:raise FormatError('illegal quadrature in session')
        p=(r.tick,r.signed_payload)
        if out and not(r.flags&0x8000) and abs(p[1]-out[-1][1])>1:
            raise FormatError('encoder discontinuity/wrap; do not bridge missing counts')
        if out and out[-1][0]==p[0]:out[-1]=p
        else:out.append(p)
    return out

def interpolate_y(tick:int,points:list[tuple[int,int]],diameter_mm:float=20.,ppr:int=4096,
                  quadrature:int=4)->float|None:
    if diameter_mm<=0 or ppr<=0 or quadrature<=0:raise ValueError('encoder scale')
    i=bisect_right(points,(tick,1<<63))-1
    if i<0:return None
    if points[i][0]==tick:count=points[i][1]
    elif i+1>=len(points):return None  # no extrapolation beyond captured evidence
    else:
        t0,p0=points[i];t1,p1=points[i+1]
        if t1<=t0:return None
        count=p0+(p1-p0)*(tick-t0)/(t1-t0)
    return count*math.pi*diameter_mm/(ppr*quadrature)

def map_samples(records:list[Record],sync_span_mm:float=92.,film_width_mm:float=80.,
                sensor_delay_ticks:float=0.) -> list[dict]:
    if film_width_mm<=0 or sync_span_mm<film_width_mm:raise ValueError('widths')
    lines=lines_from_records(records);starts=[x.sos_tick-sensor_delay_ticks for x in lines]
    enc=encoder_points(records);out=[]
    for r in records:
        if r.kind!=SAMPLE:continue
        i=bisect_right(starts,r.tick)-1
        if i<0:continue
        line=lines[i]
        if r.tick>=line.eos_tick-sensor_delay_ticks:continue
        x=x_mm(r.tick,line,sync_span_mm,sensor_delay_ticks)
        if not -film_width_mm/2<=x<film_width_mm/2:continue
        y=interpolate_y(r.tick,enc)
        # Never call a relative modulo-six line number an absolute facet identity.
        out.append({'tick':r.tick,'line_id':line.line_id,'facet_relative':line.relative_facet,
                    'facet_absolute':'UNKNOWN','x_mm':round(x,9),'y_mm':None if y is None else round(y,9),
                    'adc_a':r.a,'adc_b':r.b,'flags':r.flags,
                    'coordinate_valid':int(y is not None and not(r.flags&0x2c)),
                    'intensity_in_range':int(not(r.flags&3))})
    return out
