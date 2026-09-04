import cadquery as cq

height = 0.008
lower_diameter = 0.0492
upper_diameter = 0.048
hole_diameter = 0.008

coord_x_center = -0.046272
coord_y_center = 0.017092


solid = (cq.Workplane("XY")
         .center(coord_x_center, coord_y_center)
         .circle(lower_diameter / 2)
         .workplane(offset=height)
         .circle(upper_diameter / 2)
         .loft(combine=True)
         .faces(">Z")
         .hole(hole_diameter)
         )

show_object(solid)
