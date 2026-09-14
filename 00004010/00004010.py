import cadquery as cq
import math

mirror_signs = (-1, 1)

outer_diameter = 15
inner_hole_diameter = 8.6
half_height = 12

side_groove_height = 0.35
side_groove_length = 1.1
side_groove_spacing = 15.3

front_side_groove_inner_diameter_1 = 9.92
front_side_groove_inner_diameter_2 = 10.25
front_side_groove_height = 0.375
front_side_groove_outer_diameter_1 = 13.7
front_side_groove_outer_width = 0.326
fillet_clearance = 0.0001

track_half_straight = 8.25
track_outer_radius = 2.25
track_inner_radius = 1.5
track_surface_radius = 4.0
track_count = 5
capsule_extrusion_depth = 6
capsule_angle = 90
radial_edge_tolerance = 1e-5
radial_edge_y_limit = 10.6
track_root_fillet_radius = 0.125
track_tip_fillet_radius = 0.2

race_radius = 1.85
race_half_width = 0.295
positive_half_width = 10
positive_half_length = 30
positive_half_height = 12
bore_limit_depth = 30

straight_ball_index_start = -13
straight_ball_index_last = 13
straight_ball_radius = 0.316
straight_ball_x = 1.856
straight_ball_pitch = 0.6375
straight_ball_z = 3.9
end_ball_radius = 0.282
end_ball_angles_degrees = (26, 47, 68, 89)
sphere_start_angle_degrees = -90
square_exponent = 2

rotation_origin = (0, 0, 0)
rotation_axis_end = (0, 1, 0)
cylinder_centering = (True, True, False)
positive_half_centering = (False, True, False)

outer_radius = outer_diameter / 2
inner_radius = inner_hole_diameter / 2
side_groove_position_from_XZ = side_groove_spacing / 2
side_groove_position_from_YZ = outer_radius - side_groove_height
front_side_groove_inner_radius_1 = front_side_groove_inner_diameter_1 / 2
front_side_groove_inner_radius_2 = front_side_groove_inner_diameter_2 / 2
front_side_groove_outer_radius_1 = front_side_groove_outer_diameter_1 / 2
front_side_groove_outer_radius_2 = front_side_groove_outer_radius_1 + front_side_groove_outer_width
outer_fillet_band_width = outer_radius - front_side_groove_outer_radius_2
fillet_radius = outer_fillet_band_width / 2 - fillet_clearance
front_side_groove_cut_depth = -front_side_groove_height
side_groove_offset = -side_groove_position_from_XZ
side_groove_extrusion_depth = -side_groove_length
side_groove_cut_radius_1 = outer_radius
side_groove_cut_radius_2 = outer_radius - side_groove_height
race_outer_radius = race_radius + race_half_width
race_inner_radius = race_radius - race_half_width
end_cap_distance = track_half_straight + race_radius
straight_ball_index_stop = straight_ball_index_last + 1
end_ball_center_radius = track_surface_radius + end_ball_radius
end_ball_center_radius_squared = end_ball_center_radius ** square_exponent

smallest_radius_selector = cq.selectors.RadiusNthSelector(
    0, directionMax=False
)
second_smallest_radius_selector = cq.selectors.RadiusNthSelector(
    1, directionMax=False
)
oter_fillet_selector = cq.selectors.AndSelector(
    smallest_radius_selector, second_smallest_radius_selector
)
largest_radius_selector = cq.selectors.RadiusNthSelector(-1)
second_largest_radius_selector = cq.selectors.RadiusNthSelector(-2)
outer_fillet_edge_selector = largest_radius_selector + second_largest_radius_selector

bearing_body_half = (
    cq.Workplane('XZ')
    .cylinder(half_height, outer_radius, centered=cylinder_centering)
    .faces('<Y')
    .workplane()
    .hole(inner_hole_diameter)
    .faces('<Y')
    .workplane()
    .circle(front_side_groove_inner_radius_1)
    .circle(front_side_groove_inner_radius_2)
    .cutBlind(front_side_groove_cut_depth)
    .faces('<Y')
    .workplane()
    .circle(front_side_groove_outer_radius_1)
    .circle(front_side_groove_outer_radius_2)
    .cutBlind(front_side_groove_cut_depth)
)

fillet_selector = bearing_body_half.faces('<Y').edges(outer_fillet_edge_selector)
bearing_body_half = fillet_selector.fillet(fillet_radius)

side_groove_cut = (
    cq.Workplane('ZX')
    .workplane(offset=side_groove_offset)
    .circle(side_groove_cut_radius_1)
    .circle(side_groove_cut_radius_2)
    .extrude(side_groove_extrusion_depth)
)

bearing_body_half = bearing_body_half.cut(side_groove_cut)
solid = bearing_body_half.mirror('XZ', union=True)


def capsule(radius):
    capsule_half_length = track_half_straight + radius
    capsule_length = capsule_half_length * 2
    capsule_diameter = radius * 2
    return (
        cq.Workplane('XY')
        .slot2D(capsule_length, capsule_diameter, capsule_angle)
        .extrude(capsule_extrusion_depth)
    )


def radial_edges(workplane, radius):
    selected_edges = []
    shape = workplane.val()
    for edge in shape.Edges():
        vertices = edge.Vertices()
        if not vertices:
            continue
        radius_checks = []
        y_checks = []
        for vertex in vertices:
            vertex_radius = math.hypot(vertex.X, vertex.Z)
            radius_difference = vertex_radius - radius
            radius_error = abs(radius_difference)
            absolute_y = abs(vertex.Y)
            radius_matches = radius_error < radial_edge_tolerance
            y_matches = absolute_y < radial_edge_y_limit
            radius_checks.append(radius_matches)
            y_checks.append(y_matches)
        if all(radius_checks) and all(y_checks):
            selected_edges.append(edge)
    return selected_edges


inner_clearance = (
    cq.Workplane('XZ')
    .circle(track_surface_radius)
    .extrude(half_height, both=True)
)
track_outer_capsule = capsule(track_outer_radius)
track_inner_capsule = capsule(track_inner_radius)
track = track_outer_capsule.cut(track_inner_capsule).cut(inner_clearance)

rotation_angles = []
for index in range(track_count):
    rotation_numerator = index * 360
    rotation_angle = rotation_numerator / track_count
    rotation_angles.append(rotation_angle)

tracks = []
for rotation_angle in rotation_angles:
    track_shape = track.val()
    rotated_track = track_shape.rotate(rotation_origin, rotation_axis_end, rotation_angle)
    tracks.append(rotated_track)
tracks_compound = cq.Compound.makeCompound(tracks)
solid = solid.union(tracks_compound)

edges = radial_edges(solid, inner_radius)
solid = solid.newObject(edges).fillet(track_root_fillet_radius)
edges = radial_edges(solid, track_surface_radius)
solid = solid.newObject(edges).fillet(track_tip_fillet_radius)

race_outer_capsule = capsule(race_outer_radius)
race_inner_capsule = capsule(race_inner_radius)
race = race_outer_capsule.cut(race_inner_capsule)
positive_half = (
    cq.Workplane('XY')
    .box(
        positive_half_width,
        positive_half_length,
        positive_half_height,
        centered=positive_half_centering,
    )
)
bore_limit = cq.Workplane('XZ').circle(inner_radius).extrude(bore_limit_depth, both=True)
race = race.intersect(positive_half)

end_cap_points = []
for sign in mirror_signs:
    end_cap_y = sign * end_cap_distance
    end_cap_point = (0, end_cap_y)
    end_cap_points.append(end_cap_point)

end_caps = (
    cq.Workplane('XY')
    .pushPoints(end_cap_points)
    .circle(race_half_width)
    .extrude(capsule_extrusion_depth)
)
race = race.union(end_caps).intersect(bore_limit)

cuts = []
for rotation_angle in rotation_angles:
    race_shape = race.val()
    rotated_cut = race_shape.rotate(rotation_origin, rotation_axis_end, rotation_angle)
    cuts.append(rotated_cut)
cuts_compound = cq.Compound.makeCompound(cuts)
solid = solid.cut(cuts_compound)

balls = []
for index in range(straight_ball_index_start, straight_ball_index_stop):
    ball_y = index * straight_ball_pitch
    ball_center = cq.Vector(straight_ball_x, ball_y, straight_ball_z)
    ball = cq.Solid.makeSphere(
        straight_ball_radius, ball_center, angleDegrees1=sphere_start_angle_degrees
    )
    balls.append(ball)

for sign in mirror_signs:
    for degrees in end_ball_angles_degrees:
        angle = math.radians(degrees)
        angle_cosine = math.cos(angle)
        angle_sine = math.sin(angle)
        x = race_radius * angle_cosine
        y_offset = race_radius * angle_sine
        y_distance = track_half_straight + y_offset
        y = sign * y_distance
        x_squared = x ** square_exponent
        z_squared = end_ball_center_radius_squared - x_squared
        z = math.sqrt(z_squared)
        ball_center = cq.Vector(x, y, z)
        ball = cq.Solid.makeSphere(
            end_ball_radius, ball_center, angleDegrees1=sphere_start_angle_degrees
        )
        balls.append(ball)

all_balls = []
for rotation_angle in rotation_angles:
    for ball in balls:
        rotated_ball = ball.rotate(rotation_origin, rotation_axis_end, rotation_angle)
        all_balls.append(rotated_ball)
balls_compound = cq.Compound.makeCompound(all_balls)
solid = solid.union(balls_compound)

show_object(solid)


