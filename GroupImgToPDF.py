#!/usr/bin/env python
from pylatex import Document, Figure, NoEscape, MiniPage
import math

def GroupImgToPdf(plot_files,outname,ncols,captionBool,margin="0.5in"):
    # Write some LaTeX
    tex = Document(geometry_options={"margin":margin},page_numbers=False)

    indexing = GetIndexing(len(plot_files),ncols)

    for irow in indexing:
        these_plots = [plot_files[iplot] for iplot in irow]
        with tex.create(Figure(position='h!')) as fig:
            for plot in these_plots:
                fig.add_image(plot,width=NoEscape(r'%s\textwidth'%(0.97/len(these_plots))))
                if captionBool:
                    fig.add_caption(plot)

    tex.generate_pdf(outname,clean_tex=False)

def GetIndexing(nplots,ncols):
    indexing = []
    nrows = math.ceil(nplots/ncols)
    for irows in range(0,nrows):
        if irows <= (nrows-1):
            indexing.append([irows + i for i in range(ncols)])
        else:
            indexing.append([irows + i for i in range(nplots%ncols)])
    return indexing


if __name__ == "__main__":
    from argparse import ArgumentParser
    import glob
    parser = ArgumentParser()

    parser.add_argument('-o', metavar='F', action='store', type=str,
                    default   =   '',
                    required  =   True,
                    dest      =   'output',
                    help      =   'Output pdf name')

    parser.add_argument('-m', metavar='F', action='store', type=str,
                    default   =   '0.5in',
                    dest      =   'margin',
                    help      =   'Margin (with units)')

    parser.add_argument('--columns', metavar='F', action='store', type=int,
                    default   =   1,
                    dest      =   'columns',
                    help      =   'Number of columns per page')

    parser.add_argument('--captions', action='store_true',
                    default   =   False,
                    dest      =   'captions',
                    help      =   'Add captions with file path')

    parser.add_argument(dest = 'plotfiles', metavar='FILENAMES', type=str, nargs='+',
                    help='Plot file names')

    options = parser.parse_args()

    plots = []
    for f in options.plotfiles:
        if '*' in f:
            plots.extend(glob.glob(f))
        else:
            plots.append(f)

    GroupImgToPdf(plots,options.output,options.columns,options.captions,margin=options.margin)
