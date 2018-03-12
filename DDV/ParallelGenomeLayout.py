from __future__ import print_function, division, absolute_import, \
    with_statement, generators, nested_scopes

from datetime import datetime
from math import floor

from PIL import ImageFont

from DNASkittleUtils.CommandLineUtils import just_the_name
from DDV.TileLayout import TileLayout, font_name
from DDV.DDVUtils import LayoutLevel


class ParallelLayout(TileLayout):
    def __init__(self, n_genomes):
        # This layout is best used on one chromosome at a time.
        super(ParallelLayout, self).__init__(use_fat_headers=False, sort_contigs=False)
        # modify layout with an additional bundled column layer
        columns = self.levels[2]
        new_width = columns.thickness * n_genomes + columns.padding * 2
        self.levels = self.levels[:2]  # trim off the others
        self.levels.append(LayoutLevel("ColumnInRow", floor(10600 / new_width), levels=self.levels))  # [2]
        self.levels[2].padding = new_width - (columns.thickness - columns.padding)
        self.column_offset = columns.thickness  # steps inside a column bundle, not exactly the same as bundles steps
        # because of inter bundle padding of 18 pixels
        self.levels.append(LayoutLevel("RowInTile", 10, padding=36, levels=self.levels))  # [3]  overwrite padding from previous layer
        self.levels.append(LayoutLevel("TileColumn", 3, padding=36 * 3 * 5, levels=self.levels))  # [4]
        self.levels.append(LayoutLevel("TileRow", 999, levels=self.levels))  # [5]

        self.n_genomes = n_genomes
        self.genome_processed = 0
        self.using_background_colors = False
        self.origin = [6, self.levels[3].thickness + 6]  # start with one row for a title, but not subsequent rows
        self.column_colors = "#FFFFFF #E5F3FF #EAFFE5 #FFE7E5 #F8E5FF #FFF3E5 #FFFFE5 #FFF6E5".split()
        self.column_colors = self.column_colors[:self.n_genomes]

    def enable_fat_headers(self):
        pass  # just don't

    def process_file(self, output_folder, output_file_name, fasta_files=list()):
        assert len(fasta_files) == self.n_genomes, "List of Genome files must be same length as n_genomes"
        start_time = datetime.now()
        self.image_length = self.read_contigs_and_calc_padding(fasta_files[0])
        self.prepare_image(self.image_length)
        if self.using_background_colors:
            self.fill_in_colored_borders()
        print("Initialized Image:", datetime.now() - start_time)

        try:
            # Do inner work for two other files
            for index, filename in enumerate(fasta_files):
                if index != 0:
                    self.read_contigs_and_calc_padding(filename)
                self.color_changes_per_genome()
                self.draw_nucleotides()
                self.draw_titles()
                self.genome_processed += 1
                print("Drew File:", filename, datetime.now() - start_time)
        except Exception as e:
            print('Encountered exception while drawing nucleotides:', '\n', str(e))
        self.draw_the_viz_title(fasta_files)
        self.generate_html(output_folder, output_file_name)  # only furthest right file is downloadable
        self.output_image(output_folder, output_file_name)
        print("Output Image in:", datetime.now() - start_time)

    def color_changes_per_genome(self):
        if self.using_background_colors:
            self.change_background_color(self.genome_processed)

    def position_on_screen(self, index):
        """ In ParallelLayout, each genome is given a constant x offset in order to interleave the results of each
        genome as it is processed separately.
        """
        x, y = super(ParallelLayout, self).position_on_screen(index)
        return [x + self.column_offset * self.genome_processed, y]


    def fill_in_colored_borders(self):
        """When looking at more than one genome, it can get visually confusing as to which column you are looking at.
        To help keep track of it correctly, ParallelGenomeLayout introduces colored borders for each of the columns.
        Then instead of thinking 'I'm looking at the third column' you can think 'I'm looking at the pink column'."""
        # Step through the upper left corner of each column in the file
        column_size = self.levels[2].chunk_size
        margin = 6 // 2
        for genome_index in range(1, self.n_genomes):  # skip the white column
            self.genome_processed = genome_index
            color = self.column_colors[genome_index]
            for column_progress in range(0, self.image_length, column_size):
                left, top = self.position_on_screen(column_progress)
                left, top = max(0, left - margin), max(0, top - margin)
                right, bottom = self.position_on_screen(column_progress + column_size - 1)
                right, bottom = min(self.image.width, right + margin), min(self.image.height, bottom + margin)
                self.draw.rectangle([left, top, right, bottom], fill=color)
        self.genome_processed = 0


    def draw_the_viz_title(self, filenames):
        """Write the names of each of the source files in order so their columns can be identified with their
        column colors"""
        font = ImageFont.truetype(font_name, 380)
        titles = [just_the_name(x) for x in filenames]  # remove extension and path
        span = '      '.join(titles)
        title_spanning_width = font.getsize(span)[0]  # For centered text
        left_start = self.image.width / 2.0 - title_spanning_width / 2.0
        for genome_index in range(self.n_genomes):
            color = self.column_colors[genome_index]
            title = titles[genome_index]
            text_size = font.getsize(title)
            right = left_start + text_size[0]
            bottom = 6 + text_size[1] * 1.1
            if self.using_background_colors:
                self.draw.rectangle([left_start, 6, right, bottom], fill=color)
            self.draw.text((left_start, 6, right, bottom), title, font=font, fill=(30, 30, 30, 255))
            left_start += font.getsize(title + '      ')[0]


    def change_background_color(self, genome_processed):
        from DDV import gap_char
        def hex_to_rgb(h):
            h = h.lstrip('#')
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

        background = hex_to_rgb(self.column_colors[genome_processed])
        self.palette[gap_char] = background


    def calc_padding(self, total_progress, next_segment_length, multipart_file):
        """Parallel Layouts have a special title which describes the first (main) alignment.
        So padding for their title does not need to be included."""
        # Get original values and level
        reset_padding, title_padding, tail = super(ParallelLayout, self).calc_padding(total_progress, next_segment_length, multipart_file)
        # Remove first title
        if total_progress == 0:
            tail += title_padding
            title_padding = 0
            # i = min([i for i in range(len(self.levels)) if next_segment_length + 2600 < self.levels[i].chunk_size])
            # total_padding = total_progress + title_padding + reset_padding + next_segment_length
            # tail = self.levels[i - 1].chunk_size - total_padding % self.levels[i - 1].chunk_size - 1

        return reset_padding, title_padding, tail


    def draw_title(self, total_progress, contig):
        if total_progress != 0:
            super(ParallelLayout, self).draw_title(total_progress, contig)

