import cadquery as cq

flanged_bushing_inner_radius = 0.008 / 2
flanged_bushing_outer_radius = 0.017 / 2
flanged_bushing_height = 0.006
flanged_bushing_center = 0.04435

rod_radius = 0.006 / 2
rod_center = - 0.0503
rod_height = 0.268

shaft_radius = 0.008 / 2
shaft_length_before_collar = 0.348
shaft_collar_radius = 0.011 / 2
shaft_collar_length = 0.03
shaft_length_after_collar = 0.336
shaft_center = - 0.027
shaft_length = shaft_length_before_collar + shaft_length_after_collar
shaft_offset = 0

arm_flange_outer_radius = 0.017 / 2
arm_flange_inner_radius = 0.008 / 2
arm_flange_height = 0.001
arm_flange_groove_height = 0.0065
arm_flange_groove_radius = 0.0135 / 2
arm_flange_bigger_height = 0.0095

arm_edge = 0.015
arm_length = 0.36

flanged_bushing = (
    cq.Workplane("XZ")
    .workplane(offset = - flanged_bushing_height / 2)
    .center(flanged_bushing_center, 0)
    .cylinder(flanged_bushing_height, flanged_bushing_outer_radius)
    .circle(flanged_bushing_inner_radius)
    .cutThruAll()
)

rod = (
    cq.Workplane("XZ")
    .workplane(offset = rod_height / 2)
    .center(rod_center, 0)
    .cylinder(rod_height, rod_radius)
)

shaft_before_collar = (
    cq.Workplane("XZ")
    .workplane()
    .center(shaft_center, 0)
    .circle(shaft_radius)
    .extrude(-shaft_length_before_collar)
)

shaft_after_collar = (
    cq.Workplane("XZ")
    .workplane()
    .center(shaft_center, 0)
    .circle(shaft_radius)
    .extrude(shaft_length_after_collar)
)

shaft_collar = (
    cq.Workplane("XZ")
    .workplane()
    .center(shaft_center, 0)
    .circle(shaft_collar_radius)
    .extrude(shaft_collar_length)
)

shaft_with_collar = (shaft_before_collar
                     .union(shaft_after_collar)
                     .union(shaft_collar)
                     )

arm_flange = (
    cq.Workplane("XZ")
    .workplane()
    .circle(arm_flange_outer_radius)
    .extrude(-arm_flange_bigger_height)
    .faces(">Y")
    .circle(arm_flange_groove_radius)
    .extrude(-arm_flange_groove_height)
    .faces(">Y")
    .circle(arm_flange_outer_radius)
    .extrude(-arm_flange_height)
    .faces(">Y")
    .circle(arm_flange_inner_radius)
    .cutThruAll()
)

arm = (cq.Workplane("XZ")
       .workplane()
       .rect(arm_edge, arm_edge)
       .extrude(arm_length)
       )

arm_with_flange = arm.union(arm_flange)

solid = (arm_with_flange
         .union(shaft_with_collar)
         .union(flanged_bushing)
         .union(rod)
         )

show_object(solid)
