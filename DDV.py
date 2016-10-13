"""
self.is an optional addon to DDV written in Python that allows you to generate a single image
for an entire genome.  It was necessary to switch platforms and languages because of intrinsic
limitations in the size of image that could be handled by: C#, DirectX, Win2D, GDI+, WIC, SharpDX,
or Direct2D. We tried a lot of options.

self.python file contains basic image handling methods.  It also contains a re-implementation of
Josiah's "Tiled Layout" algorithm which is also in DDVLayoutManager.cs.
"""
import multiprocessing
import os
import sys

print("Setting up Python...")

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    os.environ["PATH"] += os.pathsep + os.path.join(BASE_DIR, 'bin')
    os.environ["PATH"] += os.pathsep + os.path.join(BASE_DIR, 'bin', 'env')
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print('Running in:', BASE_DIR)

sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, 'bin'))
sys.path.append(os.path.join(BASE_DIR, 'bin', 'env'))

os.chdir(BASE_DIR)

multiprocessing.freeze_support()

# ----------BEGIN MAIN PROGRAM----------
__version__ = '1.0.2'

import shutil
import argparse
from http import server
from socketserver import TCPServer

from DDVUtils import create_deepzoom_stack, just_the_name, make_output_dir_with_suffix
from TileLayout import TileLayout
from ParallelGenomeLayout import ParallelLayout
from ChainParser import ChainParser
from UniqueOnlyChainParser import UniqueOnlyChainParser


if sys.platform == 'win32':
    OS_DIR = 'windows'
    EXTENSION = '.exe'
    SCRIPT = '.cmd'
else:
    OS_DIR = 'linux'
    EXTENSION = ''
    SCRIPT = ''


def query_yes_no(question, default='yes'):
    valid = {'yes': True, 'y': True, "no": False, 'n': False}

    if default is None:
        prompt = " [y/n] "
    elif default in ['yes', 'y']:
        prompt = " [Y/n] "
    elif default in ['no', 'n']:
        prompt = " [y/N] "
    else:
        raise ValueError("Invalid default answer!")

    while True:
        sys.stdout.write('\n' + question + prompt)

        choice = input().lower()

        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no'.\n")


def run_server(home_directory):
    print("Setting up HTTP Server based from", home_directory)
    os.chdir(home_directory)

    ADDRESS = "127.0.0.1"
    PORT = 8000

    handler = server.SimpleHTTPRequestHandler
    httpd = TCPServer((ADDRESS, PORT), handler)

    print("Serving at %s on port %s" %(ADDRESS, str(PORT)))
    httpd.serve_forever()


def ddv(args):
    if getattr(sys, 'frozen', False):
        BASE_DIR = os.path.dirname(sys.executable)
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SERVER_HOME = os.path.join(BASE_DIR, 'www-data', 'dnadata')

    if not args.layout_type and args.run_server:
        run_server(SERVER_HOME)
        sys.exit(0)

    base_path = os.path.join(SERVER_HOME, args.output_name)
    if args.layout_type == "NONE":  # DEPRECATED: Shortcut for old visualizations to create dz stack from existing large image
        output_dir = make_output_dir_with_suffix(base_path, '')
        print("Creating Deep Zoom Structure for Existing Image...")
        create_deepzoom_stack(args.image, os.path.join(output_dir, 'GeneratedImages', "dzc_output.xml"))
        print("Done creating Deep Zoom Structure.")
        # TODO: Copy over html structure
        sys.exit(0)
    elif args.layout_type == "tiled":  # Typical Use Case
        # TODO: allow batch of tiling layout by chromosome
        output_dir = make_output_dir_with_suffix(base_path, '')
        create_tile_layout_viz_from_fasta(args, args.fasta, output_dir)
        sys.exit(0)
    # views that support batches of chromosomes
    if args.layout_type == "parallel":  # Parallel genome column layout OR quad comparison columns
        if not args.chain_file:  # life is simple
            # TODO: allow batch of tiling layout by chromosome
            output_dir = make_output_dir_with_suffix(base_path, '')
            create_parallel_viz_from_fastas(args, len(args.extra_fastas) + 1, output_dir, [args.fasta] + args.extra_fastas)
            sys.exit(0)
        else:  # parse chain files, possibly in batch
            chain_parser = ChainParser(chain_name=args.chain_file,
                                       second_source=args.extra_fastas[0],
                                       first_source=args.fasta,
                                       output_prefix=base_path,
                                       trial_run=args.trial_run,
                                       swap_columns=False,
                                       include_translocations=not args.skip_translocations,
                                       squish_gaps=args.squish_gaps)
            print("Creating Gapped and Unique Fastas from Chain File...")
            batches = chain_parser.parse_chain(args.chromosomes)
            del chain_parser
            print("Done creating Gapped and Unique.")
            for batch in batches:  # multiple chromosomes, multiple views
                create_parallel_viz_from_fastas(args, len(batch.fastas), batch.output_folder, batch.fastas)
            sys.exit(0)
    elif args.layout_type == "unique":
        """UniqueOnlyChainParser(chain_name='hg38ToPanTro4.over.chain',
                               first_source='HongKong\\hg38.fa',
                               second_source='',
                               output_folder_prefix='Hg38_unique_vs_panTro4_')"""
        unique_chain_parser = UniqueOnlyChainParser(chain_name=args.chain_file,
                                                    second_source=args.fasta,
                                                    first_source=args.fasta,
                                                    output_prefix=base_path,
                                                    trial_run=args.trial_run,
                                                    include_translocations=not args.skip_translocations)
        batches = unique_chain_parser.parse_chain(args.chromosomes)
        print("Done creating Gapped and Unique Fastas.")
        del unique_chain_parser
        for batch in batches:
            create_tile_layout_viz_from_fasta(args, batch.fastas[0], batch.output_folder)
        sys.exit(0)

    elif args.layout_type == "original":
        raise NotImplementedError("Original layout is not implemented!")
    else:
        raise NotImplementedError("What you are trying to do is not currently implemented!")


def create_parallel_viz_from_fastas(args, n_genomes, output_dir, fastas):
    print("Creating Large Comparison Image from Input Fastas...")
    layout = ParallelLayout(n_genomes=n_genomes)
    layout.process_file(output_dir, just_the_name(output_dir), fastas)
    layout_final_output_location = layout.final_output_location
    del layout
    try:
        for extra_fasta in fastas:
            shutil.copy(extra_fasta, os.path.join(output_dir, os.path.basename(extra_fasta)))
    except shutil.SameFileError:
        pass  # not a problem
    print("Done creating Large Image and HTML.")
    print("Creating Deep Zoom Structure from Generated Image...")
    create_deepzoom_stack(os.path.join(output_dir, layout_final_output_location),
                          os.path.join(output_dir, 'GeneratedImages', "dzc_output.xml"))
    print("Done creating Deep Zoom Structure.")
    if args.run_server:
        run_server(output_dir)


def create_tile_layout_viz_from_fasta(args, fasta, output_dir):
    print("Creating Large Image from Input Fasta...")
    layout = TileLayout()
    layout.process_file(fasta, output_dir, just_the_name(output_dir))
    layout_final_output_location = layout.final_output_location
    del layout
    try:
        shutil.copy(fasta, os.path.join(output_dir, os.path.basename(fasta)))
    except shutil.SameFileError:
        pass  # not a problem
    print("Done creating Large Image and HTML.")
    print("Creating Deep Zoom Structure from Generated Image...")
    create_deepzoom_stack(os.path.join(output_dir, layout_final_output_location), os.path.join(output_dir, 'GeneratedImages', "dzc_output.xml"))
    print("Done creating Deep Zoom Structure.")
    if args.run_server:
        run_server(output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(usage="%(prog)s [options]",
                                     description="Creates visualizations of FASTA formatted DNA nucleotide data.",
                                     add_help=True)

    parser = argparse.ArgumentParser(prog='DDV.exe')
    parser.add_argument('-n', '--update_name', dest='update_name', help='Query for the name of this program as known to the update server', action='store_true')
    parser.add_argument('-v', '--version', dest='version', help='Get current version of program.', action='store_true')

    parser.add_argument("-i", "--image",
                        type=str,
                        help="Path to already laid out big image to process with DeepZoom. No layout will be performed if an image is passed in.",
                        dest="image")
    parser.add_argument("-f", "--fasta",
                        type=str,
                        help="Path to main FASTA file to process into new visualization.",
                        dest="fasta")
    parser.add_argument("-o", "--outname",
                        type=str,
                        help="What to name the output folder (not a path). Defaults to name of the fasta file.",
                        dest="output_name")
    parser.add_argument("-l", "--layout",
                        type=str,
                        help="The type of layout to perform. Will autodetect between Tiled and Parallel. Really only need if you want the Original DDV layout or Unique only layout.",
                        choices=["original", "tiled", "parallel", "unique"],
                        dest="layout_type")  # Don't set a default so we can do error checking on it later
    parser.add_argument("-x", "--extrafastas",
                        nargs='+',
                        type=str,
                        help="Path to secondary FASTA files to process when doing Parallel layout.",
                        dest="extra_fastas")
    parser.add_argument("-c", "--chainfile",
                        type=str,
                        help="Path to Chain File when doing Parallel Comparisons layout.",
                        dest="chain_file")
    parser.add_argument("-ch", "--chromosomes",
                        nargs='+',
                        type=str,
                        help="Chromosome to parse from Chain File. NOTE: Defaults to 'chrY' for testing.",
                        dest="chromosomes")
    parser.add_argument("-s", "--runserver",
                        action='store_true',
                        help="Run Web Server after computing.",
                        dest="run_server")
    parser.add_argument("-t", "--skip_translocations",
                        action='store_true',
                        help="Don't include translocation in the alignment.",
                        dest="skip_translocations")
    parser.add_argument("-g", "--squish_gaps",
                        action='store_true',
                        help="If two gaps are approximately the same size, subtract the intersection.",
                        dest="squish_gaps")
    parser.add_argument("-q", "--trial_run",
                        action='store_true',
                        help="Only show the first 10Mbp.  This is faster.",
                        dest="trial_run")

    args = parser.parse_args()

    # Respond to an updater query
    if args.update_name:
        print("DDV")
        sys.exit(0)
    elif args.version:
        print(__version__)
        sys.exit(0)

    # Errors
    if args.layout_type == "original":
        parser.error("The 'original' layout is not yet implemented in Python!")  # TODO: Implement the original layout

    if args.image and (args.fasta or args.layout_type or args.extra_fastas or args.chain_file):
        parser.error("No layout will be performed if an existing image is passed in! Please only define an existing 'image' and the desired 'outfile'.")
    if not args.image and not args.fasta and not args.run_server:
        parser.error("Please either define a 'fasta' file or an 'image' file!")

    if args.extra_fastas and not args.layout_type:
        args.layout_type = "parallel"
    if args.layout_type and (args.layout_type == "parallel" or args.layout_type == "unique") and not args.extra_fastas:
        parser.error("When doing a Parallel or Unique layout, you must at least define 'extrafastas' if not 'extrafastas' and a 'chainfile'!")
    if args.chromosomes and not args.chain_file:
        parser.error("Listing 'Chromosomes' is only relevant when parsing Chain Files!")
    if args.extra_fastas and "parallel" not in args.layout_type:
        parser.error("The 'extrafastas' argument is only used when doing a Parallel layout!")
    if args.chain_file and args.layout_type not in ["parallel", "unique"]:
        parser.error("The 'chainfile' argument is only used when doing a Parallel or Unique layout!")
    if args.chain_file and len(args.extra_fastas) > 1:
        parser.error("Chaining more than two samples is currently not supported! Please only specify one 'extrafastas' when using a Chain input.")
    if args.layout_type == "unique" and not args.chain_file:
        parser.error("You must have a 'chainfile' to make a Unique layout!")

    # Set post error checking defaults
    if not args.image and not args.layout_type and args.fasta:
        args.layout_type = "tiled"
    if args.image and not args.layout_type:
        args.layout_type = "NONE"

    if args.chain_file and not args.chromosomes:
        args.chromosomes = ['chrY']

    if args.output_name and args.chain_file and args.output_name[-1] != '_':
        args.output_name += '_'  # prefix should always end with an underscore

    # Set dependent defaults
    if not args.output_name and args.layout_type:
        if args.chain_file:
            args.output_name = 'Parallel_%s_and_%s_' % (just_the_name(args.fasta), just_the_name(args.extra_fastas[0]))
            if args.layout_type == "unique":
                args.output_name = '%s_unique_vs_%s_' % (just_the_name(args.fasta), just_the_name(args.extra_fastas[0]))
        else:
            args.output_name = just_the_name(args.fasta or args.image)

    ddv(args)
