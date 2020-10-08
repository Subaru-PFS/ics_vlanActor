from datetime import datetime
import fitsio
import numpy
import draw


def composite(file):

    n_cameras = 6
    composite_image_size = 512

    with fitsio.FITS(file) as fits:

        header = fits['cam1'].read_header()
        timestamp = datetime.strptime(header['DATE'], '%Y%m%d%H%M%S%f').timestamp()
        exposure_time = header['EXPTIME']
        exposure_type = 1  # normal

        image = numpy.zeros((composite_image_size, composite_image_size), dtype=numpy.uint16)

        objects = fits['objects'].read()
        n_objects = len(objects)

        nx = ny = int(numpy.sqrt(n_objects))
        if nx * ny < n_objects:
            nx += 1
            if nx * ny < n_objects:
                ny += 1
        assert nx * ny >= n_objects

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

        for obj in objects:

            icam, iobj, m00, xc, yc, m11, m20, m02, x, y, pk, bg = obj
            icam -= 1
            iobj -= 1
            x, y = int(round(xc)), int(round(yc))
            sx = get_size(composite_image_size, nx, ix)
            sy = get_size(composite_image_size, ny, iy)
            x0 = max(0, min(x - sx // 2, fits[icam + 1][:, :].shape[1] - sx))
            y0 = max(0, min(y - sy // 2, fits[icam + 1][:, :].shape[0] - sy))
            cropped = draw.crop(fits[icam + 1][:, :], (x0, y0), (sx, sy))

            def put_crosshair(image, position, size=5, grayscale=0):

                x, y = position
                d = size // 2
                draw.line(image, (x - d, y), (x + d, y), 1, grayscale)
                draw.line(image, (x, y - d), (x, y + d), 1, grayscale)

            # grayscale for crosshairs
            grayscale = 0

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
            draw.line(image, (x, 0), (x, composite_image_size - 1), 1, grayscale)
        for iy in range(ny - 1):
            y = get_end(composite_image_size, ny, iy)
            draw.line(image, (0, y), (composite_image_size - 1, y), 1, grayscale)

    return timestamp, exposure_time, exposure_type, image


if __name__ == '__main__':

    import sys

    infile = '/proc/self/fd/0'
    outfile = 'vlan.fits'
    if len(sys.argv) > 1:
        infile = sys.argv[1]
        if len(sys.argv) > 2:
            outfile = sys.argv[2]
    _, _, _, image = composite(infile)
    with fitsio.FITS(outfile, 'rw', clobber=True) as fits:
        fits.write(image, compress='rice')
