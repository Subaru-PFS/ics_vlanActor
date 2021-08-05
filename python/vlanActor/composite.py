from datetime import datetime
import fitsio
import numpy
import draw


def composite(input_file, detected_objects=None, identified_objects=None):

    n_cameras = 6
    composite_image_size = 512

    with fitsio.FITS(input_file) as fits:

        header = fits['cam1'].read_header()
        timestamp = datetime.strptime(header['DATE'], '%Y-%m-%dT%H:%M:%S').timestamp()
        exposure_time = header['EXPTIME']
        exposure_type = 1  # normal

        image = numpy.zeros((composite_image_size, composite_image_size), dtype=numpy.uint16)

        if detected_objects is None:
            try:
                detected_objects = fits['objects'].read()
            except:
                detected_objects = []
        n_objects = len(detected_objects)

        nx = ny = int(numpy.sqrt(n_objects))
        if nx * ny < n_objects:
            nx += 1
            if nx * ny < n_objects:
                ny += 1
        assert nx * ny >= n_objects

        if identified_objects is None:
            identified_objects = [(i, i, 0, 0, 0, 0, x[3], x[4]) for i, x in enumerate(detected_objects)]

        def get_start(n, m, i):

            a = n - (m - 1)
            k = a // m
            r = a % m
            return i * (k + 1) + min(i, r)

        def get_end(n, m, i):

            return get_start(n, m, i + 1) - 1

        def get_size(n, m, i):

            return get_end(n, m, i) - get_start(n, m, i)

        ix, iy = 0, 0

        for _iobj, obj in enumerate(detected_objects):

            icam, iobj, m00, xc, yc, m11, m20, m02, x, y, pk, bg, *_ = obj
            icam -= 1
            iobj -= 1
            x, y = int(round(xc)), int(round(yc))
            sx = get_size(composite_image_size, nx, ix)
            sy = get_size(composite_image_size, ny, iy)
            x0 = max(0, min(x - sx // 2, fits[icam + 1][:, :].shape[1] - sx))
            y0 = max(0, min(y - sy // 2, fits[icam + 1][:, :].shape[0] - sy))
            cropped = draw.crop(fits[icam + 1][:, :], (x0, y0), (sx, sy))

            # check if this object has been identified or not;
            # the first column of identified_objects is an index to detected_objects
            i = next((i for i, v in enumerate(identified_objects) if v[0] == _iobj), None)

            if i is not None:

                x, y = [int(round(x)) for x in identified_objects[i][6:]]

                def put_crosshair(image, position, size=8, grayscale=0):

                    x, y = position
                    d = size // 2
                    draw.line(image, (x - d, y), (x + d, y), grayscale)
                    draw.line(image, (x, y - d), (x, y + d), grayscale)

                # grayscale for crosshairs
                grayscale = 2 ** 15 - 1

                # draw a crosshair where this guide object is expected to be
                put_crosshair(cropped, (x - x0, y - y0), grayscale=grayscale)

            # grayscale for annotations
            grayscale = 2 ** 15 - 1

            fontsize = 8

            text = 'CAM{}'.format(icam + 1)
            draw.text(cropped, (1, cropped.shape[0] - 2), text, grayscale)
            text = 'OBJ{}'.format(iobj + 1)
            draw.text(cropped, (1, fontsize - 1), text, grayscale)

            image[get_start(composite_image_size, ny, iy):get_end(composite_image_size, ny, iy), get_start(composite_image_size, nx, ix):get_end(composite_image_size, nx, ix)] = cropped[:, :]

            ix += 1
            if ix == nx:
                ix = 0
                iy += 1
                if iy == ny:
                    iy = 0

        # grayscale for grids
        grayscale = 2 ** 15 - 1

        for ix in range(nx - 1):
            x = get_end(composite_image_size, nx, ix)
            draw.line(image, (x, 0), (x, composite_image_size - 1), grayscale)
        for iy in range(ny - 1):
            y = get_end(composite_image_size, ny, iy)
            draw.line(image, (0, y), (composite_image_size - 1, y), grayscale)

    return timestamp, exposure_time, exposure_type, image


if __name__ == '__main__':

    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('--tile-id', type=int, required=True, help='tile identifier')
    parser.add_argument('--frame-id', type=int, required=True, help='frame identifier')
    parser.add_argument('--obswl', type=float, default=0.62, help='wavelength of observation (um)')
    parser.add_argument('--input-file', required=True, help='')
    parser.add_argument('--output-file', required=True, help='')
    args, _ = parser.parse_known_args()

    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(name='composite')

    from field_acquisition import acquire_field

    _, _, _, *values = acquire_field(args.tile_id, args.frame_id, obswl=args.obswl, verbose=True, logger=logger)
    _, detected_objects, identified_objects, *_ = values

    _, _, _, image = composite(args.input_file, detected_objects=detected_objects, identified_objects=identified_objects)
    with fitsio.FITS(args.output_file, 'rw', clobber=True) as fits:
        fits.write(image, compress='rice')
