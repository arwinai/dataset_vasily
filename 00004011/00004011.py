import cadquery as cq

lower_plate_length = 0.23
lower_plate_height = 0.006

upper_plate_offset = 0.02 + lower_plate_height
upper_plate_lower_length = 0.214
upper_plate_lower_height = 0.002
upper_plate_upper_length = 0.203
upper_plate_upper_height = 0.002

hole_radius = 0.003 / 2
rect_length_for_through_hole = 0.209

holes_center_list = [
    (-0.10025, -0.0205),
    (-0.06975, -0.0205),
    (0.10025, -0.0205),
    (0.06975, -0.0205),
    (-0.10025, 0.0905),
    (-0.06975, 0.0905),
    (0.10025, 0.0905),
    (0.06975, 0.0905),
    (-0.01875, 0.0245),
    (-0.01875, 0.0455),
]


lower_plate = (cq.Workplane("XY")
        .box(lower_plate_length, lower_plate_length, lower_plate_height, centered=(True, True, False))
        .faces(">Z")
        .workplane()
        .pushPoints(holes_center_list)
        .circle(hole_radius)
        .cutThruAll()
         )


upper_plate = (cq.Workplane("XY")
               .workplane(offset=upper_plate_offset)
               .box(upper_plate_lower_length, upper_plate_lower_length, upper_plate_lower_height, centered=(True, True, False))
               .faces(">Z")
               .workplane()
               .box(upper_plate_upper_length, upper_plate_upper_length, upper_plate_upper_height, centered=(True, True, False))
               )

solid = lower_plate.union(upper_plate)

solid = (solid
         .faces(">Z")

         .rect(rect_length_for_through_hole, rect_length_for_through_hole, forConstruction=True)
         .vertices()
         .circle(hole_radius)
         .cutThruAll()
         )