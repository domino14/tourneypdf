import argparse
import json
import math
import sys
import qrcode

import cairo
import webcolors

from fetch_tourney import get_tournament

qrcode_urls = set()
url_uniqueness_trunc = 3


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


def create_simple_qr(data, error_correction=qrcode.constants.ERROR_CORRECT_L):
    # Instantiate QRCode object with desired settings
    qr = qrcode.QRCode(
        version=1,  # You might start with version 1 for the simplest QR code
        error_correction=error_correction,
        box_size=10,  # Adjust box size for the size of each square (the smaller, the more squares)
        border=4,  # The border around the QR code
    )

    # Add data to the QR code
    qr.add_data(data)
    qr.make(fit=True)  # Fit to the smallest possible QR code version

    # Create an image from the QR Code instance
    img = qr.make_image(fill_color="black", back_color="white")

    return img


# 8.5 x 11 inches in points (612 x 792)


def gen_single_player_scorecard(ctx, yoffset, div, nrounds, meta, pidx, show_opponents):
    idtrunc = div["players"]["persons"][pidx]["id"][:url_uniqueness_trunc]
    qrcode_url = f"https://woogles.io{meta['metadata']['slug']}/{idtrunc}"
    if qrcode_url in qrcode_urls:
        raise Exception("url not unique")
    qrcode_urls.add(qrcode_url)
    qrcode_img = create_simple_qr(qrcode_url)
    # Convert QR code to 'RGBA' format
    qr_rgba = qrcode_img.convert("RGBA")

    qr_bytes = bytearray(qr_rgba.tobytes())

    qrsurface = cairo.ImageSurface.create_for_data(
        qr_bytes, cairo.FORMAT_ARGB32, qr_rgba.width, qr_rgba.height, qr_rgba.width * 4
    )

    ctx.save()
    ctx.translate(480, yoffset + 10)
    ctx.scale(0.20, 0.20)

    ctx.set_source_surface(qrsurface, 0, 0)
    ctx.paint()
    ctx.restore()

    player = div["players"]["persons"][pidx]
    player_name = player["id"].split(":")[1]
    player_rating = player["rating"]

    black = format_color("black")
    ctx.new_path()
    ctx.set_font_size(20)
    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
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
    ctx.show_text(meta["metadata"]["name"])

    # line for player and name
    ctx.set_font_size(12)
    ctx.move_to(80, yoffset + 45)
    ctx.line_to(200, yoffset + 45)
    ctx.stroke()

    ctx.move_to(80, yoffset + 40)
    ctx.show_text(f"{player_name}  ({player_rating})")

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
    if nrounds == 8:
        rect_ht = 35
    for i in range(nrounds):
        ctx.rectangle(25, yoffset + 100 + (i * rect_ht), 535, rect_ht)
        ctx.stroke()
        ctx.arc(  # circle around player's number
            100,
            yoffset + 100 + (i * rect_ht) + (rect_ht / 2),
            (rect_ht - 4) / 2,
            0,
            2 * math.pi,
        )
        ctx.stroke()
        ctx.set_font_size(18)

        ctx.move_to(50, yoffset + 125 + (i * rect_ht))
        ctx.show_text(str(i + 1))
        ctx.move_to(35, yoffset + 130 + (i * rect_ht) + (5 if nrounds == 7 else 0))
        ctx.set_font_size(8)
        ctx.show_text("1st        2nd")

        for x in xs:
            ctx.move_to(x - 5, yoffset + 100 + (i * rect_ht))  # 340 to 380 at end
            ctx.line_to(x - 5, yoffset + 100 + (i * rect_ht) + rect_ht)
            ctx.stroke()
    # Draw known pairings
    if show_opponents:
        ctx.set_font_size(12)
        for k, v in div["pairing_map"].items():
            if pidx in v["players"]:
                rd = v["round"]
                for i in v["players"]:
                    if i != pidx:
                        opp = i
                        opp_name = div["players"]["persons"][opp]["id"].split(":")[1]
                rdY = yoffset + 125 + (rd * rect_ht) - (2 if nrounds == 8 else 0)
                rdX = 97
                if len(str(opp + 1)) > 1:
                    rdX = 93
                ctx.move_to(rdX, rdY)
                ctx.show_text(str(opp + 1))
                ctx.move_to(140, rdY)
                ctx.show_text(opp_name)
        ctx.new_path()


def gen_scorecard(div, nrounds, meta, p1, p2, show_opponents):
    yoffset = 0
    divname = div["division"]
    fname = f"{divname}{p1+1}-{p2+1}.pdf"
    if p1 == p2:
        fname = f"{divname}{p1+1}.pdf"

    surface = cairo.PDFSurface(fname, 612, 792)
    ctx = cairo.Context(surface)

    if p1 != p2:
        for idx, pidx in enumerate([p1, p2]):
            yoffset = idx * 396

            gen_single_player_scorecard(
                ctx, yoffset, div, nrounds, meta, pidx, show_opponents
            )

    else:
        yoffset = 200
        gen_single_player_scorecard(
            ctx, yoffset, div, nrounds, meta, p1, show_opponents
        )

    surface.flush()


def gen_scorecards(tourney, show_opponents):
    for divname, div in tourney["t"]["divisions"].items():
        nrounds = len(div["round_controls"])
        if nrounds <= 8:
            skip = 2
        else:
            skip = 1
        # nrounds = 7
        for i in range(0, len(div["players"]["persons"]), skip):
            gen_scorecard(
                div, nrounds, tourney["meta"], i, i + skip - 1, show_opponents
            )

    # ctx.rectangle(200, 100, 50, 50)  # x y w h
    # second_color = format_color("black")
    # ctx.set_line_width(3)
    # ctx.set_source_rgba(*second_color)
    # ctx.stroke()
    # surface.flush()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="gen",
        description="Generates physical scorecards for Woogles tournaments",
    )

    parser.add_argument("tid_or_file")  # positional argument
    parser.add_argument("-o", "--opponents", action="store_true")
    args = parser.parse_args()

    tid = args.tid_or_file
    if tid.endswith(".json"):
        with open(tid) as f:
            tourney = json.load(f)
    else:
        tourney = get_tournament(tid)
    # print(json.dumps(tourney))
    gen_scorecards(tourney, args.opponents)
