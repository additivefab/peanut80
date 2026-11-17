"""R5.2 collector change: trapezoid PMMA light-guide plate replacing the R5 8x10 taper rod (C06).
Stand-alone; does not rebuild or overwrite the R5-PDR1 CAD set. Needs cadquery and ezdxf.
Coordinates are the R5 global frame (X scan, Y feed, Z up); cavity axis at Y=0, Z=83.1."""
import json,math
from pathlib import Path
import cadquery as cq, ezdxf
ROOT=Path(__file__).resolve().parents[2]
g=json.loads((ROOT/'engineering/parameters.json').read_text())['collector_guide_r52']
zc=json.loads((ROOT/'engineering/parameters.json').read_text())['cavity_center_z']
win,wout,t,L=g['input_width_x'],g['output_width_x'],g['thickness_z'],g['length_y']
y0=g['input_face_y'];y1=y0-L
prof=[(-win/2,y0),(win/2,y0),(wout/2,y1),(-wout/2,y1)]
plate=cq.Workplane('XY').workplane(offset=zc-t/2).polyline(prof).close().extrude(t)
out=ROOT/'cad/step';cq.exporters.export(plate,str(out/'C06_R52_plate.step'))
# review context: liner tube with top slot and the new side slot, plate, PMT effective window disc
liner=(cq.Workplane('YZ').workplane(offset=-60).center(0,zc).circle(23.4).circle(20).extrude(120))
liner=liner.cut(cq.Workplane('XY').box(104,1.2,10).translate((0,0,zc+21)))
liner=liner.cut(cq.Workplane('XY').box(g['cavity_side_slot'][0],8,g['cavity_side_slot'][1]).translate((0,-21.5,zc)))
pmt=cq.Workplane('XZ').workplane(offset=-g['pmt_window_y']).center(0,zc).circle(4).extrude(-0.5)
asm=cq.Assembly();asm.add(liner,name='C02_liner_R52_side_slot');asm.add(plate,name='C06_R52_plate');asm.add(pmt,name='PMT_effective_dia8')
asm.save(str(out/'Collector_R52_review.step'))
doc=ezdxf.new('R2010');doc.units=ezdxf.units.MM;m=doc.modelspace()
m.add_lwpolyline(prof,close=True,dxfattribs={'layer':'OUTLINE'})
m.add_text(f'C06-R52 PMMA plate t={t} mm; all six faces optical polish; no chamfer >0.1',dxfattribs={'height':2,'layer':'NOTE'}).set_placement((-50,y0+4))
doc.saveas(ROOT/'cad/dxf/C06_R52_plate.dxf')
bb=plate.val().BoundingBox()
print('plate volume mm3',round(plate.val().Volume(),1),'bbox',[round(v,2) for v in (bb.xmin,bb.ymin,bb.zmin,bb.xmax,bb.ymax,bb.zmax)],'valid',plate.val().isValid())
