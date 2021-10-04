from datetime import datetime
import fitsio
import numpy
import draw


class IMAGE:

    CENTER = (511.5 + 24, 511.5 + 9)

    class ORIENTATION:
        LANDSCAPE = 0
        PORTRAIT = 1


def composite(input_file, orientation=IMAGE.ORIENTATION.LANDSCAPE, center=(IMAGE.CENTER, ) * 6):

    composite_image_size = 512

    with fitsio.FITS(input_file) as fits:

        cameras = []
        timestamp = 0
        exposure_time = 0
        exposure_type = 1  # normal

        for icam in range(6):

            header = fits['cam{}'.format(icam + 1)].read_header()
            if header['NAXIS'] > 0:
                cameras.append(icam)
                timestamp = datetime.strptime(header['DATE'], '%Y-%m-%dT%H:%M:%S').timestamp()
                exposure_time = header['EXPTIME']
                #exposure_type = 1  # normal

        n_cameras = len(cameras)

        nx = ny = int(numpy.sqrt(n_cameras))
        if nx * ny < n_cameras:
            if orientation:
                nx += 1
            else:
                ny += 1
            if nx * ny < n_cameras:
                if orientation:
                    ny += 1
                else:
                    nx += 1
        assert nx * ny >= n_cameras

        def get_start(n, m, i):

            a = n - (m - 1)
            k = a // m
            r = a % m
            return i * (k + 1) + min(i, r)

        def get_end(n, m, i):

            return get_start(n, m, i + 1) - 1

        def get_size(n, m, i):

            return get_end(n, m, i) - get_start(n, m, i)

        image = numpy.zeros((composite_image_size, composite_image_size), dtype=numpy.uint16)
        overlay = numpy.zeros_like(image)

        ix, iy = 0, 0

        for icam in cameras:

            x, y = int(round(center[icam][0])), int(round(center[icam][1]))
            sx = get_size(composite_image_size, nx, ix)
            sy = get_size(composite_image_size, ny, iy)
            x0 = max(0, min(x - sx // 2, fits[icam + 1][:, :].shape[1] - sx))
            y0 = max(0, min(y - sy // 2, fits[icam + 1][:, :].shape[0] - sy))
            cropped = draw.crop(fits[icam + 1][:, :], (x0, y0), (sx, sy))

            # origin of crop in composite image/overlay pixel coordinates (u, v)
            u = get_start(composite_image_size, nx, ix)
            v = get_start(composite_image_size, ny, iy)

            fontsize = 8

            text = 'CAM{} ({},{})'.format(icam + 1, x, y)
            draw.text(overlay, (u + 1, v + (fontsize - 1)), text, 1)

            image[v:v + sy, u:u + sx] = cropped[:, :]

            ix += 1
            if ix == nx:
                ix = 0
                iy += 1
                if iy == ny:
                    iy = 0

        for ix in range(nx - 1):
            x = get_end(composite_image_size, nx, ix)
            draw.line(overlay, (x, 0), (x, composite_image_size - 1), 1)
        for iy in range(ny - 1):
            y = get_end(composite_image_size, ny, iy)
            draw.line(overlay, (0, y), (composite_image_size - 1, y), 1)

        # grayscale for overlay
        grayscale = max(numpy.amax(image), 1)

        image = numpy.maximum(image, grayscale * overlay)

    return timestamp, exposure_time, exposure_type, image


if __name__ == '__main__':

    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('--input-file', required=True, help='')
    parser.add_argument('--output-file', required=True, help='')
    args, _ = parser.parse_known_args()

    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(name='composite_simple')

    _, _, _, image = composite(args.input_file)
    with fitsio.FITS(args.output_file, 'rw', clobber=True) as fits:
        fits.write(image, compress='rice')
