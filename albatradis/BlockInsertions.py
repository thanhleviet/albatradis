'''Driver class'''
import logging
import os
import sys
import time
import shutil
from albatradis.TradisGeneInsertSites import TradisGeneInsertSites
from albatradis.PrepareInputFiles     import PrepareInputFiles
from albatradis.PrepareEMBLFile       import PrepareEMBLFile
from albatradis.TradisEssentiality    import TradisEssentiality
from albatradis.TradisComparison      import TradisComparison
from albatradis.PlotLog               import PlotLog
from albatradis.PlotMasking           import PlotMasking
from albatradis.BlockIdentifier       import BlockIdentifier
from albatradis.GeneAnnotator        import GeneAnnotator

class PlotEssentiality:
	def __init__(self, plotfile_obj,gene_insert_sites_filename, tradis_essentiality_filename, type, only_essential_filename):
		self.plotfile_obj = plotfile_obj
		self.gene_insert_sites_filename = gene_insert_sites_filename
		self.tradis_essentiality_filename = tradis_essentiality_filename
		self.only_essential_filename = only_essential_filename
		self.type = type
		
class PlotAllEssentiality:
	def __init__(self, forward, reverse, combined, embl_filename):
		self.forward = forward
		self.reverse = reverse
		self.combined = combined
		self.embl_filename = embl_filename

class BlockInsertions:
	def __init__(self, logger,plotfiles, minimum_threshold, window_size, window_interval, verbose, minimum_logfc, pvalue, prefix, minimum_logcpm, minimum_block,span_gaps, emblfile, report_decreased_insertions, strict_signal, use_annotation, prime_feature_size):
		self.logger            = logger
		self.plotfiles         = plotfiles
		self.minimum_threshold = minimum_threshold
		self.window_size       = window_size
		self.window_interval   = window_interval
		self.verbose           = verbose
		self.minimum_logfc     = minimum_logfc
		self.pvalue            = pvalue
		self.prefix            = prefix
		self.minimum_logcpm    = minimum_logcpm
		self.minimum_block     = minimum_block
		self.span_gaps         = span_gaps
		self.emblfile          = emblfile  
		self.report_decreased_insertions = report_decreased_insertions
		self.strict_signal     = strict_signal
		self.use_annotation    = use_annotation
		self.prime_feature_size = prime_feature_size
		
		self.genome_length = 0
		self.forward_plotfile = ""
		self.reverse_plotfile = ""
		self.combined_plotfile = ""
		self.output_plots = {}
		self.blocks = []
		
		if self.verbose:
			self.logger.setLevel(logging.DEBUG)
		else:
			self.logger.setLevel(logging.ERROR)
			
		if not os.path.exists(self.prefix ):
			os.makedirs(self.prefix )
		
	def run(self):
		plotfile_objects = self.prepare_input_files()
		essentiality_files = self.run_essentiality(plotfile_objects)
		
		self.run_comparisons(essentiality_files)
		self.output_plots = self.mask_plots()
		self.genes = self.gene_statistics(self.forward_plotfile, self.reverse_plotfile, self.combined_plotfile, self.window_size)
		self.cleanup(plotfile_objects, essentiality_files)
		
		return self
		
	def prepare_input_files(self):
		plotfile_objects = {}
		
		self.annotation_file = PrepareEMBLFile(self.plotfiles[0], self.minimum_threshold, self.window_size, self.window_interval, self.use_annotation, self.prime_feature_size, self.emblfile).create_file()
		
		for plotfile in self.plotfiles:
			p = PrepareInputFiles(plotfile, self.minimum_threshold)
			p.create_all_files()
			p.embl_filename = self.annotation_file
			plotfile_objects[plotfile] = p
			
			if self.verbose:
				print("Forward plot:\t" + p.forward_plot_filename)
				print("reverse plot:\t" + p.reverse_plot_filename)
				print("combined plot:\t" + p.combined_plot_filename)
				print("Embl:\t" + self.annotation_file)
			
			self.genome_length = p.genome_length()
		return plotfile_objects
	
	def essentiality(self, plotfile_objects, plotfile, filetype):
		g = TradisGeneInsertSites(plotfile_objects[plotfile].embl_filename, getattr(plotfile_objects[plotfile], filetype + "_plot_filename"), self.verbose)
		g.run()
		e = TradisEssentiality(g.output_filename, self.verbose)
		e.run()
		pe = PlotEssentiality(plotfile, g.output_filename, e.output_filename, filetype, e.essential_filename)
		
		if self.verbose:
			print("Essentiality:\t" + filetype + "\t" + e.output_filename)
		return pe
		
	def run_essentiality(self, plotfile_objects):
		essentiality_files = {}
		for plotfile in plotfile_objects:
			f = self.essentiality(plotfile_objects, plotfile, 'forward')
			r = self.essentiality(plotfile_objects, plotfile, 'reverse')
			c = self.essentiality(plotfile_objects, plotfile, 'combined')
			e = plotfile_objects[plotfile].embl_filename	
			essentiality_files[plotfile] = PlotAllEssentiality(f,r,c,e)

		return essentiality_files
		
	def run_comparisons(self, essentiality_files):
		self.forward_plotfile = self.generate_logfc_plot('forward',essentiality_files)
		self.reverse_plotfile = self.generate_logfc_plot('reverse',essentiality_files)
		self.combined_plotfile = self.generate_logfc_plot('combined',essentiality_files)
			
	def generate_logfc_plot(self, analysis_type, essentiality_files):
		files = [getattr(essentiality_files[plotfile], analysis_type).tradis_essentiality_filename for plotfile in self.plotfiles]
		
		only_ess_files = [getattr(essentiality_files[plotfile], analysis_type).only_essential_filename for plotfile in self.plotfiles]
		
		annotation_files = [essentiality_files[plotfile].embl_filename for plotfile in self.plotfiles]
		mid = int(len(files)  / 2)
		
		t = TradisComparison(files[:mid],files[mid:], self.verbose, self.minimum_block, only_ess_files[:mid], only_ess_files[mid:])
		t.run()
		p = PlotLog(t.output_filename, self.genome_length, self.minimum_logfc, self.pvalue, self.minimum_logcpm, self.window_size, self.span_gaps, self.report_decreased_insertions, annotation_files[0])
		p.construct_plot_file()
		renamed_csv_file  = os.path.join(self.prefix, analysis_type + ".csv")
		renamed_plot_file = os.path.join(self.prefix, analysis_type + ".plot")
		
		shutil.copy(t.output_filename, renamed_csv_file)
		shutil.copy(p.output_filename, renamed_plot_file)
		os.remove(t.output_filename)
		os.remove(p.output_filename)
		
		if self.verbose:
			print("Comprison:\t"+ renamed_csv_file)
			print("Plot log:\t"+ renamed_plot_file)
		return renamed_plot_file
		
	def gene_statistics(self,forward_plotfile, reverse_plotfile, combined_plotfile, window_size):
		b = BlockIdentifier(combined_plotfile, forward_plotfile, reverse_plotfile, window_size)
		blocks = b.block_generator()
		
		annotationfile = self.emblfile 
		if self.use_annotation:
			annotationfile = self.annotation_file 
		
		genes = GeneAnnotator(self.annotation_file , blocks).annotate_genes()
		intergenic_blocks = [block for block in blocks if block.intergenic]
		
		if len(genes) == 0:
			return []
		
		block_filename = os.path.join(self.prefix, "gene_report.csv")
		with open(block_filename, 'w') as bf:
			bf.write(str(genes[0].header())+"\n")
			for i in genes:
				bf.write(str(i)+"\n")
				
			for b in intergenic_blocks:
				bf.write(str(b)+"\n")
				
		if self.verbose:
			print(genes[0].header())		
			for i in genes:
				print(i)
				
			for b in intergenic_blocks:
				print(b)
		
		return genes
		
	def mask_plots(self):
		pm = PlotMasking(self.plotfiles, self.combined_plotfile, self.strict_signal )
		renamed_plot_files = {}
		
		for pfile in pm.output_plot_files:
			original_basefile  = os.path.join(self.prefix, os.path.basename(pfile) )
			renamed_file = original_basefile.replace('.gz','')
			shutil.copy(pm.output_plot_files[pfile], renamed_file)
			os.remove(pm.output_plot_files[pfile])
			renamed_plot_files[pfile] = renamed_file
			
			if self.verbose:
				print("Masked: " + renamed_file )
		return renamed_plot_files
		
		
	def cleanup(self, plotfile_objects, essentiality_files):
		
		# initial plot files 
		for p in plotfile_objects.values():
			os.remove(p.forward_plot_filename)
			os.remove(p.reverse_plot_filename)
			os.remove(p.combined_plot_filename)
			if os.path.exists(p.embl_filename):
				shutil.move(p.embl_filename, os.path.join(self.prefix, "annotation.embl") )
		
