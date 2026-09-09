import cadquery as cq

body_outer_radius = 20.5 / 2
body_inner_radius = 10 / 2
body_inner_height = 1.55
body_outer_chamfer_height = 0.9
body_inside_radius = 13.4 / 2
body_outside_radius = 16.5 / 2
body_half_height_before_chamfer = 3.45
body_half_height_inside_before_chamfer = 2.8
body_half_height = body_half_height_before_chamfer + body_outer_chamfer_height


coil_hole_diameter = 4
coil_hole_chamfer = 0.25
coil_outer_chamfer = 0.25
coil_outer_radius = 13 / 2
coil_half_height = 5 / 2
coil_groove_radius_inner = 7.8 / 2
coil_groove_radius_outer = 9.2 / 2
coil_groove_height = 0.125

torus_radius = 2.33 / 2
torus_radius_from_center = 6.17 / 2 + torus_radius
torus_center_x = -4.25
torus_rect_length = torus_radius * 2
torus_rect_width = 0.7


body_outer_cut = (cq.Workplane("XY")
                  .circle(body_outer_radius)
                  .circle(body_outside_radius)
                  .extrude(body_half_height_before_chamfer)
                  )

body_inner_cut = (cq.Workplane("XY")
                  .circle(body_inside_radius)
                  .extrude(body_half_height_inside_before_chamfer)
                  .faces(">Z")
                  .circle(body_inner_radius)
                  .extrude(body_inner_height)
                  )

body = (cq.Workplane("XY")
        .cylinder(body_half_height, body_outer_radius, centered=(True, True, False))
        )

body = (body
        .cut(body_outer_cut)
        .cut(body_inner_cut)
        .mirror("XY", union=True)
        )

coil = (cq.Workplane("XY")
        .cylinder(coil_half_height, coil_outer_radius, centered=(True, True, False))
        .faces(">Z")
        .workplane()
        .hole(coil_hole_diameter)
        .faces(">Z")
        .workplane()
        .circle(coil_groove_radius_inner)
        .circle(coil_groove_radius_outer)
        .cutBlind(-coil_groove_height)
        )

coil_hole_chamfer_selector = (coil
                         .faces(">Z")
                         .edges(cq.selectors.RadiusNthSelector(0, directionMax=True))
                         )

coil = coil_hole_chamfer_selector.chamfer(coil_hole_chamfer)

coil_outer_chamfer_selector = (coil
                               .faces(">Z")
                               .edges(cq.selectors.RadiusNthSelector(0, directionMax=False))
                               )

coil = coil_outer_chamfer_selector.chamfer(coil_outer_chamfer)

coil = coil.mirror("XY", union=True)


torus_sketch = (cq.Sketch()
                .rect(torus_rect_width, torus_rect_length)
                .circle(torus_radius)
                .clean()
                )

torus_cut = (cq.Workplane("XZ")
    .center(torus_center_x, 0)
    .placeSketch(torus_sketch)
    .revolve(360, (-torus_center_x, 0), (-torus_center_x, 1))
)

coil = coil.cut(torus_cut)

solid = body.union(coil)

show_object(solid)
