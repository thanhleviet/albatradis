import unittest
import os
import logging
from tradistron.TradisTron import TradisTron
import shutil
import cProfile, pstats, io

test_modules_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(test_modules_dir, 'data','tradistron')

class TestOptions:
	def __init__(self, plotfiles, minimum_threshold, window_size,window_interval, verbose, prefix, minimum_logcpm, minimum_logfc, pvalue, iterations, dont_normalise_plots,minimum_block,span_gaps, emblfile ):
		self.plotfiles = plotfiles
		self.minimum_threshold = minimum_threshold
		self.window_size = window_size
		self.window_interval = window_interval
		self.verbose = verbose	
		self.prefix = prefix
		self.minimum_logcpm = minimum_logcpm
		self.minimum_logfc = minimum_logfc
		self.pvalue = pvalue
		self.iterations = iterations
		self.dont_normalise_plots = dont_normalise_plots
		self.minimum_block = minimum_block
		self.span_gaps = span_gaps
		self.emblfile = emblfile

class TestTradisTron(unittest.TestCase):
	
	def test_small_real(self):
		case = os.path.join(data_dir, 'small_case.insert_site_plot.gz')
		control = os.path.join(data_dir, 'small_control.insert_site_plot.gz')
		emblfile = os.path.join(data_dir, 'annotation.embl')
		
		#pr = cProfile.Profile()
		#pr.enable()
		
		t = TradisTron(TestOptions([case, control], 3, 100, 100, False, 'testoutput', 1, 1, 1, 1, True,1,0, emblfile))
		self.assertTrue(t.run())
		
		#pr.disable()
		#s = io.StringIO()
		#sortby = 'cumulative'
		#ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
		#ps.print_stats()
		#print(s.getvalue())
		
		
		self.assertTrue(os.path.exists('testoutput_1'))
		shutil.rmtree("testoutput_1")
		
		
	def test_small_2iterations(self):
		case = os.path.join(data_dir, 'small_case.insert_site_plot.gz')
		control = os.path.join(data_dir, 'small_control.insert_site_plot.gz')
		emblfile = os.path.join(data_dir, 'annotation.embl')
		t = TradisTron(TestOptions([case, control], 3, 100, 100, False, 'testoutput', 1, 1, 1, 2, False,1,0, emblfile))
		self.assertTrue(t.run())
		self.assertTrue(os.path.exists('testoutput_1'))
		shutil.rmtree("testoutput_1")
		self.assertTrue(os.path.exists('testoutput_2'))
		shutil.rmtree("testoutput_2")
		
	#def test_big_real(self):
	#	case = os.path.join(data_dir, 'big_case.insert_site_plot.gz')
	#	control = os.path.join(data_dir, 'big_control.insert_site_plot.gz')
	#	t = TradisTron(TestOptions([case, control], 3, 100, 100, False, 'testoutput', 1, 1,1,1 ,1))
	#	self.assertTrue(t.run())
	#	self.assertTrue(os.path.exists('testoutput_1'))
	#	shutil.rmtree("testoutput_1")