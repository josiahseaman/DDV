"""
self.is an optional addon to DDV written in Python that allows you to generate a single image
for an entire genome.  It was necessary to switch platforms and languages because of intrinsic
limitations in the size of image that could be handled by: C#, DirectX, Win2D, GDI+, WIC, SharpDX,
or Direct2D. We tried a lot of options.

self.python file contains basic image handling methods.  It also contains a re-implementation of
Josiah's "Tiled Layout" algorithm which is also in DDVLayoutManager.cs.
"""
import os
import sys
import shutil
import argparse

from http import server

from DDVUtils import create_deepzoom_stack
from TileLayout import TileLayout
from ParallelGenomeLayout import ParallelLayout
from ChainParser import ChainParser


def ddv(args):
    if getattr(sys, 'frozen', False):
        BASE_DIR = os.path.dirname(sys.executable)
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    output_dir = os.path.join(BASE_DIR, "www-data", "dnadata", args.output_name)

    print("Creating Chromosome Output Directory...")
    os.makedirs(output_dir, exist_ok=True)
    print("Done creating Directories.")

    if not args.layout_type:  # Shortcut for old visualizations to create dz stack from existing large image
        print("Creating Deep Zoom Structure for Existing Image...")
        create_deepzoom_stack(args.image, os.path.join(output_dir, 'GeneratedImages', "dzc_output.xml"))
        shutil.copy(args.image, os.path.join(output_dir, os.path.basename(args.image)))
        print("Done creating Deep Zoom Structure.")
        # TODO: Copy over html structure
        sys.exit(0)
    elif args.layout_type == "tiled":  # Typical Use Case
        print("Creating Large Image from Input Fasta...")
        layout = TileLayout()
        layout.process_file(args.input_fasta, output_dir, args.output_name)
        shutil.copy(args.input_fasta, os.path.join(output_dir, os.path.basename(args.input_fasta)))
        print("Done creating Large Image and HTML.")

        print("Creating Deep Zoom Structure from Generated Image...")
        create_deepzoom_stack(os.path.join(output_dir, layout.final_output_location), os.path.join(output_dir, 'GeneratedImages', "dzc_output.xml"))
        print("Done creating Deep Zoom Structure.")

        if args.run_server:
            handler_class = server.BaseHTTPRequestHandler
            server.test(HandlerClass=handler_class, port=8000, bind='')

        sys.exit(0)
    elif args.layout_type == "parallel":  # Parallel genome column layout OR quad comparison columns
        n_genomes = len(args.extra_fastas) + 1

        if args.chain_file:
            print("Created Gapped and Unique Fastas from Chain File...")
            chain_parser = ChainParser(args.input_fasta, args.extra_fastas[0], args.chain_file, output_dir)
            chain_parser.parse_chain(args.chromosomes)
            n_genomes = 4
            args.extra_fastas = chain_parser.extra_generated_fastas
            args.fasta = args.extra_fastas.pop()
            print("Done creating Gapped and Unique Fastas.")

        print("Creating Large Comparison Image from Input Fastas...")
        layout = ParallelLayout(n_genomes=n_genomes)
        layout.process_file(args.input_fasta, output_dir, args.output_name, args.extra_fastas)
        shutil.copy(args.input_fasta, os.path.join(output_dir, os.path.basename(args.input_fasta)))
        for extra_fasta in args.extra_fastas:
            shutil.copy(extra_fasta, os.path.join(output_dir, os.path.basename(extra_fasta)))
        print("Done creating Large Image and HTML.")

        print("Creating Deep Zoom Structure from Generated Image...")
        create_deepzoom_stack(os.path.join(output_dir, layout.final_output_location), os.path.join(output_dir, 'GeneratedImages', "dzc_output.xml"))
        print("Done creating Deep Zoom Structure.")

        if args.run_server:
            handler_class = server.BaseHTTPRequestHandler
            server.test(HandlerClass=handler_class, port=8000, bind='')

        sys.exit(0)
    elif args.layout_type == "original":
        raise NotImplementedError("Original layout is not implemented!")
    else:
        raise NotImplementedError("What you are trying to do is not currently implemented!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(usage="%(prog)s [options]",
                                     description="Creates visualizations of FASTA formatted DNA nucleotide data.",
                                     add_help=True)

    parser.add_argument("-i", "--image",
                        type=str,
                        help="Path to already laid out big image to process with DeepZoom. No layout will be performed if an image is passed in.",
                        dest="image")
    parser.add_argument("-f", "--fasta",
                        type=str,
                        help="Path to main FASTA file to process into new visualization.",
                        dest="input_fasta")
    parser.add_argument("-o", "--outname",
                        type=str,
                        help="What to name the DeepZoom output DZI file (not a path).",
                        dest="output_name")
    parser.add_argument("-l", "--layout",
                        type=str,
                        help="The type of layout to perform. Will autodetect between Tiled and Parallel. Really only need if you want the Original DDV layout.",
                        choices=["original", "tiled", "parallel"],
                        dest="layout_type")  # Don't set a default so we can do error checking on it later
    parser.add_argument("-x", "--extrafastas",
                        nargs='+',
                        type=str,
                        help="Path to secondary FASTA file to process when doing Parallel Comparisons layout.",
                        dest="extra_fastas")
    parser.add_argument("-c", "--chainfile",
                        type=str,
                        help="Path to Chain File when doing Parallel Comparisons layout.",
                        dest="chain_file")
    parser.add_argument("-ch", "--chromosomes",
                        nargs='+',
                        type=str,
                        help="Chromosome to parse from Chain File. NOTE: Defaults to 'chr21' for testing.",
                        dest="chromosomes")
    parser.add_argument("-s", "--server",
                        action='store_true',
                        help="Run Web Server after computing.",
                        dest="run_server")

    args = parser.parse_args()

    # Errors
    if args.layout_type == "original":
        parser.error("The 'original' layout is not yet implemented in Python!")  # TOOD: Implement the original layout

    if args.image and (args.input_fasta or args.layout_type or args.extra_fastas or args.chain_file):
        parser.error("No layout will be performed if an existing image is passed in! Please only define an existing 'image' and the desired 'outfile'.")
    if not args.image and not args.input_fasta:
        parser.error("Please either define a 'fasta' file or an 'image' file!")

    if args.layout_type == "parallel" and not args.extra_fastas:
        parser.error("When doing a Parallel layout, you must at least define 'extrafastas' if not 'extrafastas' and a 'chainfile'!")
    if args.extra_fastas and not args.layout_type:
        args.layout_type = "parallel"
    if args.chromosomes and not args.layout_type == "parallel" or not args.chain_file:
        parser.error("Listing 'Chromosomes' is only relevant when parsing Chain Files!")
    if args.extra_fastas and args.layout_type != "parallel":
        parser.error("The 'extrafastas' argument is only used when doing a Parallel layout!")
    if args.chain_file and args.layout_type != "parallel":
        parser.error("The 'chainfile' argument is only used when doing a Parallel layout!")
    if args.chain_file and len(args.extra_fastas) > 1:
        parser.error("Chaining more than two samples is currently not supported! Please only specify one 'extrafastas' when using a Chain input.")

    # Set post error checking defaults
    if not args.image and not args.layout_type:
        args.layout_type = "tiled"

    if args.chain_file and not args.chromosomes:
        args.chromosomes = ['chr21']

    # Set dependent defaults
    if not args.output_name:
        if args.chain_file:
            args.output_name = os.path.splitext(os.path.basename(args.input_fasta))[0] + '_AND_' + os.path.splitext(os.path.basename(args.extra_fastas[0]))[0]
        else:
            args.output_name = os.path.splitext(os.path.basename(args.input_fasta or args.image))[0]

    ddv(args)
