import cadquery as cq
from cadquery.selectors import BoxSelector

rod_radius = 4
rod_fillet = 0.5

rod_length_1 = 350

rod_center_2 = 100
rod_length_2 = 370

rod_center_3 = 200
rod_center_3_relative = rod_center_3 - rod_center_2
rod_length_3 = 400

bounding_box_coord_1 = (-rod_radius, -rod_length_3 / 2, -rod_radius)
bounding_box_coord_2 = (rod_center_3 + rod_radius, rod_length_3 / 2 + 1, rod_radius)

solid = (cq.Workplane("XZ")
         .cylinder(rod_length_1, rod_radius)
         .workplane()
         .center(rod_center_2, 0)
         .cylinder(rod_length_2, rod_radius)
         .workplane()
         .center(rod_center_3_relative, 0)
         .cylinder(rod_length_3, rod_radius)
         )

solid = (solid
        .edges(BoxSelector(bounding_box_coord_1, bounding_box_coord_2))
        .chamfer(rod_fillet)
         )

show_object(solid)