import argparse
import json
import math
import qrcode

import cairo
import webcolors
from gooey import Gooey, local_resource_path

from fetch_tourney import get_tournament


class URLNotUniqueException(Exception):
    pass


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


class ScorecardCreator:
    def __init__(self, tourney, show_opponents: bool, show_seeds: bool):
        self.tourney = tourney
        self.show_opponents = show_opponents
        self.show_seeds = show_seeds
        self.url_uniqueness_trunc = 2
        self.qrcode_urls = set()

    def reset(self):
        self.qrcode_urls = set()

    def place_qr_code(self, ctx, url):
        self.qrcode_urls.add(url)
        qrcode_img = create_simple_qr(url)
        # Convert QR code to 'RGBA' format
        qr_rgba = qrcode_img.convert("RGBA")

        qr_bytes = bytearray(qr_rgba.tobytes())

        qrsurface = cairo.ImageSurface.create_for_data(
            qr_bytes,
            cairo.FORMAT_ARGB32,
            qr_rgba.width,
            qr_rgba.height,
            qr_rgba.width * 4,
        )

        ctx.save()
        ctx.translate(495, 10)
        ctx.scale(0.20, 0.20)

        ctx.set_source_surface(qrsurface, 0, 0)
        ctx.paint()
        ctx.restore()

    def draw_name_and_tourney_header(self, ctx, player, pidx, tourney_name):
        player_name = player["id"].split(":")[1]
        player_rating = player["rating"]

        black = format_color("black")
        ctx.new_path()
        ctx.set_font_size(20)
        ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        player_name_x = 25
        if self.show_seeds:
            # circle with number
            ctx.arc(50, 50, 25, 0, 2 * math.pi)
            ctx.set_line_width(1)
            ctx.set_source_rgba(*black)
            ctx.stroke()

            xidx = 45
            if len(str(pidx + 1)) > 1:
                xidx = 40
            ctx.move_to(xidx, 56)
            ctx.show_text(str(pidx + 1))
            player_name_x = 80

        ctx.move_to(360, 56)
        ctx.show_text(tourney_name)

        ctx.move_to(225, 75)
        ctx.set_font_size(12)
        ctx.show_text("Enter scores and view standings (scan with phone):")
        # line for player and name
        ctx.set_font_size(20)
        ctx.move_to(player_name_x, 56)
        ctx.show_text(f"{player_name}  ({player_rating})")
        ctx.set_font_size(12)

    def draw_known_pairings(self, ctx, div, pidx, rect_ht, nrounds):
        ctx.set_font_size(12)
        for k, v in div["pairing_map"].items():
            if pidx in v["players"]:
                rd = v["round"]
                first = True
                opp = None
                opp_name = None
                for place, pairedidx in enumerate(v["players"]):
                    if pairedidx != pidx:
                        opp = pairedidx
                        opp_name = div["players"]["persons"][opp]["id"].split(":")[1]
                        if place == 0:
                            first = False
                if opp is None:
                    # self-pairing
                    opp = pidx
                    opp_name = v["outcomes"][0].title()
                rdY = 125 + (rd * rect_ht) - (2 if nrounds == 8 else 0)
                rdX = 97
                if len(str(opp + 1)) > 1:
                    rdX = 93
                if self.show_seeds:
                    ctx.move_to(rdX, rdY)
                    ctx.show_text(str(opp + 1))
                    ctx.move_to(140, rdY)
                else:
                    ctx.move_to(rdX, rdY)
                ctx.show_text(opp_name)
                # Circle 1st or 2nd
                y = 130 + (rd * rect_ht) + (5 if nrounds == 7 else 0) - 2
                ctx.new_sub_path()
                if first:
                    ctx.arc(40, y, 8, 0, 2 * math.pi)
                else:
                    ctx.arc(70, y, 8, 0, 2 * math.pi)
                ctx.stroke()
        ctx.new_path()

    def draw_row(self, ctx, i, rect_ht, nrounds, fields):
        ctx.rectangle(25, 100 + (i * rect_ht), 535, rect_ht)
        ctx.stroke()
        if self.show_seeds:
            ctx.arc(  # circle around player's number
                100,
                100 + (i * rect_ht) + (rect_ht / 2),
                (rect_ht - 4) / 2,
                0,
                2 * math.pi,
            )
            ctx.stroke()

        # Round number
        ctx.set_font_size(18)
        ctx.move_to(50, 125 + (i * rect_ht))
        ctx.show_text(str(i + 1))
        ctx.move_to(35, 130 + (i * rect_ht) + (5 if nrounds == 7 else 0))
        ctx.set_font_size(8)
        ctx.show_text("1st        2nd")

        last_field = len(fields)
        if i != 0:
            last_field = len(fields) - 1

        for f in fields[1:last_field]:
            ctx.move_to(f[0] - 5, 100 + (i * rect_ht))  # 340 to 380 at end
            ctx.line_to(f[0] - 5, 100 + (i * rect_ht) + rect_ht)
            ctx.stroke()
        # Deal with spread box.
        if i > 0:
            f = fields[last_field]
            ctx.move_to(f[0] - 5, 100 + (i * rect_ht))
            ctx.line_to(f[0] - 5, 100 + (i * rect_ht) + rect_ht / 2)
            ctx.stroke()
            ctx.move_to(
                fields[last_field - 1][0] - 5, 100 + (i * rect_ht) + rect_ht / 2
            )
            ctx.line_to(560, 100 + (i * rect_ht) + rect_ht / 2)
            ctx.stroke()
            ctx.move_to(
                fields[last_field - 1][0] - 2, 100 + (i * rect_ht) + 7 * (rect_ht / 8)
            )
            ctx.set_font_size(12)
            ctx.show_text("Cumulative:")

    def gen_single_player_scorecard(self, ctx, div, nrounds, meta, pidx):
        player = div["players"]["persons"][pidx]
        idtrunc = player["id"][: self.url_uniqueness_trunc]
        qrcode_url = f"https://woogles.io{meta['metadata']['slug']}?es={idtrunc}"
        if qrcode_url in self.qrcode_urls:
            raise URLNotUniqueException()
        self.place_qr_code(ctx, qrcode_url)
        self.draw_name_and_tourney_header(ctx, player, pidx, meta["metadata"]["name"])

        # header row
        ctx.rectangle(25, 80, 535, 20)
        ctx.stroke()

        fields = [
            (35, "Round"),
            (85, "Opponent"),
            (300, "Won"),
            (335, "Lost"),
            (370, "Your Score"),
            (440, "Opp Score"),
            (510, "Spread"),
        ]

        for field in fields:
            ctx.move_to(field[0], 95)
            ctx.show_text(field[1])

        # header lines
        for f in fields[1:]:
            ctx.move_to(f[0] - 5, 80)
            ctx.line_to(f[0] - 5, 100)

        rect_ht = 40
        if nrounds == 8:
            rect_ht = 35
        for i in range(nrounds):
            self.draw_row(ctx, i, rect_ht, nrounds, fields)

        # Draw known pairings
        if self.show_opponents:
            self.draw_known_pairings(ctx, div, pidx, rect_ht, nrounds)

    def gen_scorecard(self, surface, ctx, div, nrounds, meta, p1, p2):
        if p1 != p2:
            for idx, pidx in enumerate([p1, p2]):
                ctx.save()
                ctx.translate(0, idx * 396)
                self.gen_single_player_scorecard(ctx, div, nrounds, meta, pidx)
                ctx.restore()
            surface.show_page()  # Add a new page for the next scorecard
        else:
            ctx.save()
            ctx.translate(0, 200)
            self.gen_single_player_scorecard(ctx, div, nrounds, meta, p1)
            ctx.restore()
            surface.show_page()  # Add a new page for the next scorecard

        surface.flush()

    def gen_scorecards(self):
        for divname, div in self.tourney["t"]["divisions"].items():
            nrounds = len(div["round_controls"])
            skip = 2 if nrounds <= 8 else 1
            fname = f"{divname}_scorecards.pdf"
            # 8.5 x 11 inches in points (612 x 792)
            surface = cairo.PDFSurface(fname, 612, 792)
            ctx = cairo.Context(surface)

            for i in range(0, len(div["players"]["persons"]), skip):
                end = i + skip - 1
                if end > len(div["players"]["persons"]) - 1:
                    end = i
                self.gen_scorecard(
                    surface,
                    ctx,
                    div,
                    nrounds,
                    self.tourney["meta"],
                    i,
                    end,
                )
            surface.finish()


@Gooey(
    program_name="Tournament Manager for Woogles",
    image_dir=local_resource_path("images"),
)
def main():
    parser = argparse.ArgumentParser(
        prog="gen",
        description="Generates physical scorecards for Woogles tournaments",
    )

    parser.add_argument(
        "tid_or_file",
        help="Internal Tournament ID (see the bottom of Woogles Director tools)",
    )  # positional argument
    parser.add_argument(
        "-o", "--opponents", action="store_true", help="Show opponents on scorecard"
    )
    parser.add_argument(
        "-s",
        "--seeds",
        action="store_true",
        help="Show player numbers/seeds on scorecard",
    )
    args = parser.parse_args()

    tid = args.tid_or_file
    if tid.endswith(".json"):
        with open(tid) as f:
            tourney = json.load(f)
    else:
        tourney = get_tournament(tid)
    # print(json.dumps(tourney))
    creator = ScorecardCreator(tourney, args.opponents, args.seeds)
    success = False
    while success is False:
        try:
            creator.gen_scorecards()
        except URLNotUniqueException:
            creator.reset()
            creator.url_uniqueness_trunc += 1
            print(
                "Could not create unique URL, trying new trunc length",
                creator.url_uniqueness_trunc,
            )
        else:
            success = True


if __name__ == "__main__":
    main()
