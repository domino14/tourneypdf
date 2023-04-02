import cairo
import json
import math
import webcolors
import sys
from fetch_tourney import get_tournament


# format color
def format_color(*color, **kwargs):  # color is a tuple
    alpha = 1 if "alpha" not in kwargs else kwargs["alpha"]
    if isinstance(color[0], str):
        color = color[0].strip().lower()
        if color[0] == "#":
            # assume hex
            rgb = list(webcolors.hex_to_rgb(color))
        else:
            # assume color name
            rgb = list(webcolors.name_to_rgb(color))
    elif isinstance(color, (list, tuple)):
        rgb = color[:3]  # gets first three values in list
        if len(color) == 4:
            alpha = color[3]
        too_big = [x for x in rgb if x > 1]
        if not too_big:
            return color
    else:
        rgb = [0, 0, 0]  # sets default color to black

    normalized_rgb = [x / 255 for x in rgb]
    normalized_rgb.append(alpha)

    return normalized_rgb


# 8.5 x 11 inches in points (612 x 792)


def gen_scorecard(tourney, dname, p1, p2):
    yoffset = 0
    surface = cairo.PDFSurface(
        f"surface{p1}-{p2}.pdf", 612, 792
    )  # half-height, make programmaticlater
    ctx = cairo.Context(surface)

    for idx, pidx in enumerate([p1, p2]):
        yoffset = idx * 396

        player = tourney["divisions"][dname]["players"]["persons"][pidx]
        player_name = player["id"].split(":")[1]
        player_rating = player["rating"]

        black = format_color("black")
        ctx.new_path()
        ctx.set_font_size(20)
        ctx.select_font_face(
            "Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL
        )
        # circle with number
        ctx.arc(50, yoffset + 50, 25, 0, 2 * math.pi)
        ctx.set_line_width(1)
        ctx.set_source_rgba(*black)
        ctx.stroke()

        xidx = 45
        if len(str(pidx + 1)) > 1:
            xidx = 40
        ctx.move_to(xidx, yoffset + 56)
        ctx.show_text(str(pidx + 1))

        ctx.move_to(360, yoffset + 56)
        ctx.show_text("Teaneck April Foolz")

        # line for player and name
        ctx.set_font_size(12)
        ctx.move_to(80, yoffset + 45)
        ctx.line_to(200, yoffset + 45)
        ctx.stroke()

        ctx.move_to(80, yoffset + 40)
        ctx.show_text(player_name)

        # header row
        ctx.rectangle(25, yoffset + 80, 535, 20)
        ctx.stroke()
        xs = [85, 300, 335, 380, 450, 515]

        ctx.move_to(35, yoffset + 95)
        ctx.show_text("Round")
        ctx.move_to(85, yoffset + 95)
        ctx.show_text("Opponent")
        ctx.move_to(300, yoffset + 95)
        ctx.show_text("Wins")
        ctx.move_to(335, yoffset + 95)
        ctx.show_text("Losses")
        ctx.move_to(380, yoffset + 95)
        ctx.show_text("Your Score")
        ctx.move_to(450, yoffset + 95)
        ctx.show_text("Opp Score")
        ctx.move_to(515, yoffset + 95)
        ctx.show_text("Spread")
        # header lines
        for x in xs:
            ctx.move_to(x - 5, yoffset + 80)
            ctx.line_to(x - 5, yoffset + 100)

        rect_ht = 40
        for i in range(7):
            ctx.rectangle(25, yoffset + 100 + (i * rect_ht), 535, rect_ht)
            ctx.stroke()
            ctx.arc(
                100,
                yoffset + 100 + (i * rect_ht) + (rect_ht / 2),
                18,
                0,
                2 * math.pi,
            )
            ctx.stroke()
            ctx.set_font_size(18)

            ctx.move_to(50, yoffset + 125 + (i * rect_ht))
            ctx.show_text(str(i + 1))
            ctx.move_to(35, yoffset + 135 + (i * rect_ht))
            ctx.set_font_size(8)
            ctx.show_text("1st        2nd")

            for x in xs:
                ctx.move_to(
                    x - 5, yoffset + 100 + (i * rect_ht)
                )  # 340 to 380 at end
                ctx.line_to(x - 5, yoffset + 100 + (i * rect_ht) + rect_ht)
                ctx.stroke()
        # Draw known pairings
        ctx.set_font_size(12)
        for k, v in tourney["divisions"][dname]["pairing_map"].items():
            if pidx in v["players"]:
                rd = v["round"]
                for i in v["players"]:
                    if i != pidx:
                        opp = i
                        opp_name = tourney["divisions"][dname]["players"][
                            "persons"
                        ][opp]["id"].split(":")[1]
                rdY = yoffset + 125 + (rd * rect_ht)
                rdX = 97
                if len(str(opp + 1)) > 1:
                    rdX = 93
                ctx.move_to(rdX, rdY)
                ctx.show_text(str(opp + 1))
                ctx.move_to(140, rdY)
                ctx.show_text(opp_name)
        ctx.new_path()
    surface.flush()


def gen_scorecards(tourney):
    for i in range(0, 10, 2):
        gen_scorecard(tourney, "NWL", i, i + 1)

    # ctx.rectangle(200, 100, 50, 50)  # x y w h
    # second_color = format_color("black")
    # ctx.set_line_width(3)
    # ctx.set_source_rgba(*second_color)
    # ctx.stroke()
    # surface.flush()


if __name__ == "__main__":
    tid = sys.argv[1]
    if tid.endswith(".json"):
        with open(tid) as f:
            tourney = json.load(f)
    else:
        tourney = get_tournament(tid)
    gen_scorecards(tourney)
