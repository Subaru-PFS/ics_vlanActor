from datetime import datetime
import fitsio
import numpy
import draw


def composite(input_file, detected_objects=None, identified_objects=None):

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

        if detected_objects is None:
            try:
                detected_objects = fits['objects'].read()
            except:
                detected_objects = []
        #n_objects = len(detected_objects)

        # for simulations
        n_objects = 0
        for detected_object in detected_objects:
            icam, *_ = detected_object
            # for simulations
            if icam in cameras:
                n_objects += 1

        nx = ny = int(numpy.sqrt(n_objects))
        if nx * ny < n_objects:
            ny += 1
            if nx * ny < n_objects:
                nx += 1
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

        image = numpy.zeros((composite_image_size, composite_image_size), dtype=numpy.uint16)
        overlay = numpy.zeros_like(image)

        ix, iy = 0, 0

        for _iobj, detected_object in enumerate(detected_objects):

            icam, iobj, m00, xc, yc, m11, m20, m02, x, y, pk, bg, *_ = detected_object

            # for simulations
            if icam not in cameras:
                continue

            x, y = int(round(xc)), int(round(yc))
            sx = get_size(composite_image_size, nx, ix)
            sy = get_size(composite_image_size, ny, iy)
            x0 = max(0, min(x - sx // 2, fits[icam + 1][:, :].shape[1] - sx))
            y0 = max(0, min(y - sy // 2, fits[icam + 1][:, :].shape[0] - sy))
            cropped = draw.crop(fits[icam + 1][:, :], (x0, y0), (sx, sy))

            # origin of crop in composite image/overlay pixel coordinates (u, v)
            u = get_start(composite_image_size, nx, ix)
            v = get_start(composite_image_size, ny, iy)

            # check if this object has been identified or not;
            # the first column of identified_objects is an index to detected_objects
            i = next((i for i, v in enumerate(identified_objects) if v[0] == _iobj), None)

            if i is not None:

                identified_object = identified_objects[i]
                x = int(round(identified_object[6]))
                y = int(round(identified_object[7]))

                def put_crosshair(image, position, size=8, grayscale=0):

                    x, y = position
                    d = size // 2
                    draw.line(image, (x - d, y), (x + d, y), grayscale)
                    draw.line(image, (x, y - d), (x, y + d), grayscale)

                # draw a crosshair where this guide object is expected
                put_crosshair(overlay, (u + (x - x0), v + (y - y0)), grayscale=1)

            fontsize = 8

            text = 'CAM{} OBJ{}'.format(icam + 1, iobj + 1)
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
    parser.add_argument('--design-id', type=int, required=True, help='design identifier')
    parser.add_argument('--frame-id', type=int, required=True, help='frame identifier')
    parser.add_argument('--obswl', type=float, default=0.62, help='wavelength of observation (um)')
    parser.add_argument('--input-file', required=True, help='')
    parser.add_argument('--output-file', required=True, help='')
    args, _ = parser.parse_known_args()

    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(name='composite')

    from field_acquisition import acquire_field

    _, _, _, _, _, _, *values = acquire_field(design=(args.design_id, None), frame_id=args.frame_id, obswl=args.obswl, logger=logger)
    _, detected_objects, identified_objects, *_ = values

    _, _, _, image = composite(args.input_file, detected_objects=detected_objects, identified_objects=identified_objects)
    with fitsio.FITS(args.output_file, 'rw', clobber=True) as fits:
        fits.write(image, compress='rice')
