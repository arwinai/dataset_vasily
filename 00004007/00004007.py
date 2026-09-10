import cadquery as cq
from cadquery.selectors import BoxSelector


back_base_length = 35
back_base_width = 15
back_base_height = 12
back_base_full_width = 19

back_base_cut_startpoint_y = 10.475
back_base_cut_endpoint_x = -back_base_full_width
back_base_cut_endpoint_y = 16.8
back_base_cut_radius = 7

back_base_chole_1_center_x = -7
back_base_chole_1_center_y = 10.5
back_base_chole_2_center_x = -7
back_base_chole_2_center_y = -10.5
back_base_chole_points = [
    (back_base_chole_1_center_x, back_base_chole_1_center_y),
    (back_base_chole_2_center_x, back_base_chole_2_center_y)
]
back_base_chole_hole_radius = 3.5 / 2
back_base_chole_hole_height = 8
back_base_chole_height = 4
back_base_chole_distance = 5.8


right_box_length = 12.3
right_box_width = 8.8
right_box_height = 19.7
right_box_center_x = -back_base_full_width
right_box_center_y = back_base_length / 2
right_box_upper_cut_length = 5.7
right_box_upper_cut_width = 2.6
right_box_upper_cut_height = 9


right_side_hole_center_y = 23.65
right_side_hole_center_z = 14.7
right_side_pyramid_hole_radius = 3.8 / 2
right_side_hole_radius = 3.4 / 2
right_side_hole_depth = 18.3
right_side_hole_offset = 0.7

right_pyramid_hole_depth = 4.5
right_pyramid_base_length = 9.5
right_pyramid_base_width = 2
right_pyramid_base_height = 22
right_pyramid_base_center_x = -4
right_pyramid_base_center_y = 23.65

right_pyramid_edge_length = 7
right_pyramid_edge_angle = 63
right_pyramid_start_point_x = -3
right_pyramid_start_point_y = 18.9
right_pyramid_middle_point_x = 6.25
right_pyramid_middle_point_y = 23.65
right_pyramid_end_point_x = right_pyramid_start_point_x
right_pyramid_end_point_y = 28.4
right_pyramid_radius = 3.5 / 2


front_side_edges_width = 1
front_side_edges_length = 2
front_side_chamfer_2 = 2 - 0.001
front_side_array_shift = -9.5
front_side_rods_offset = 4.5
array_data = [2, 1, 7, 1]

front_side_part_half_length = 16.5
front_side_part_width = 15
front_side_height = 22
front_side_x_offset = -3
front_side_fillet_radius = 5
front_side_staring_point_x = 1.4
selector_margin = 0.1

front_side_cut_height = 14
front_side_cut_length_1 = 10.6
front_side_cut_width_1 = 2
front_side_cut_length_2 = front_side_part_half_length
front_side_cut_width_2 = 3.1
front_side_cut_offset = front_side_height - front_side_cut_height
front_side_chamfer_1 = 1


back_base = (cq.Workplane("XY")
             .box(back_base_full_width, back_base_length, back_base_height, centered=(False, True, False))
             .mirror("YZ")
             )


back_base_corner_cut = (cq.Workplane("XY")
                 .moveTo(-back_base_width, -back_base_length / 2)
                 .lineTo(-back_base_width, back_base_cut_startpoint_y)
                 .radiusArc((back_base_cut_endpoint_x, back_base_cut_endpoint_y), -back_base_cut_radius)
                 .lineTo(-back_base_full_width, -back_base_length / 2)
                 .close()
                 .extrude(back_base_height)
                 )

back_base_chole_cut = (cq.Workplane("XY")
                       .pushPoints(back_base_chole_points)
                       .circle(back_base_chole_hole_radius)
                       .extrude(back_base_chole_hole_height)
                       .faces(">Z")
                       .workplane()
                       .pushPoints(back_base_chole_points)
                       .polygon(6, back_base_chole_distance, circumscribed=True)
                       .extrude(back_base_chole_height)
                       )

back_base = (back_base
             .cut(back_base_corner_cut)
             .cut(back_base_chole_cut)
             )


right_box = (cq.Workplane("XY")
              .center(right_box_center_x, right_box_center_y)
              .box(right_box_width, right_box_length, right_box_height, centered=(False, False, False))
             .faces(">Z")
             .workplane(centerOption="CenterOfMass")
             .rect(right_box_upper_cut_width, right_box_upper_cut_length)
             .cutBlind(-right_box_upper_cut_height)
              )


right_pyramid_base = (cq.Workplane("XY")
                 .moveTo(right_pyramid_base_center_x, right_pyramid_base_center_y)
                 .box(right_pyramid_base_width, right_pyramid_base_length, right_pyramid_base_height, centered=(True, True, False))
                 )


right_pyramid = (cq.Workplane("XY")
                 .moveTo(right_pyramid_start_point_x, right_pyramid_start_point_y)
                 .lineTo(right_pyramid_middle_point_x, right_pyramid_middle_point_y)
                 .lineTo(right_pyramid_end_point_x, right_pyramid_end_point_y)
                 .close()
                 .extrude(right_pyramid_base_height)
                 .edges(">X")
                 .fillet(right_pyramid_radius)
                 )


right_side_hole_cut = (cq.Workplane("YZ")
                       .workplane(offset=-right_side_hole_offset)
                       .moveTo(right_side_hole_center_y, right_side_hole_center_z)
                       .circle(right_side_pyramid_hole_radius)
                       .extrude(-right_pyramid_hole_depth)
                       .faces("<X")
                       .circle(right_side_hole_radius)
                       .extrude(-right_side_hole_depth)
              )

right_side = (right_box
              .union(right_pyramid_base)
              .union(right_pyramid)
              .cut(right_side_hole_cut)
              )



front_side_cut_1 = (cq.Workplane("XY")
                  .workplane(offset=front_side_cut_offset)
                  .center(front_side_staring_point_x, 0)
                  .box(front_side_cut_length_1, front_side_cut_width_1, front_side_cut_height, centered=(False, False, False))

                  )

front_side_cut_2 = (cq.Workplane("XY")
                    .workplane(offset=front_side_cut_offset)
                    .center(front_side_staring_point_x, 0)
                    .box(front_side_cut_width_2, front_side_cut_length_2, front_side_cut_height, centered=(False, False, False))
                    )

front_side_half_part = (cq.Workplane("XY")
                        .moveTo(front_side_x_offset, 0)
                        .box(front_side_part_width, front_side_part_half_length, front_side_height, centered=(False, False, False))
                        .cut(front_side_cut_1)
                        .cut(front_side_cut_2)
                   )


front_side_coord_for_selector_fillet_1 = [front_side_part_width + selector_margin,
                                       front_side_cut_width_1 +selector_margin,
                                       front_side_height + selector_margin]
front_side_coord_for_selector_fillet_2 = [front_side_part_width + front_side_x_offset - selector_margin,
                                          front_side_cut_width_1 - selector_margin,
                                          front_side_cut_offset + selector_margin
                                          ]

front_side_half_part_fillet_selector = BoxSelector(
    (front_side_coord_for_selector_fillet_1),
    (front_side_coord_for_selector_fillet_2)
)

front_side_half_part = (front_side_half_part
                        .faces(">Z")
                        .edges(cq.NearestToPointSelector((0, front_side_part_half_length / 2, front_side_height)))
                        .chamfer(front_side_chamfer_1)
)

front_side_half_part =  (front_side_half_part
                         .edges(front_side_half_part_fillet_selector)
                         .fillet(front_side_fillet_radius)
                     )

front_side_half_part_edges = (cq.Workplane("YZ")
                              .workplane(offset=front_side_rods_offset - front_side_edges_length )
                              .center(front_side_array_shift, 0)
                              .rarray(*array_data)
                              .box(front_side_edges_width, front_side_height, front_side_edges_length * 2, centered=(False, False, False))
                    )

front_side_half_part_edges = (front_side_half_part_edges
                              .edges("|Y")
                              .chamfer(front_side_chamfer_2)
                              )

front_side_part = (front_side_half_part
                   .union(front_side_half_part_edges)
                   .mirror("ZX", union=True)
                   )

solid = (back_base
         .union(right_side)
         .union(front_side_part)
         )

show_object(solid)