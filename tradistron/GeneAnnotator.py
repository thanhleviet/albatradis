from Bio import SeqIO
from tradistron.Gene import Gene
from tradistron.EMBLReader import EMBLReader

class GeneAnnotator:
	def __init__(self, annotation_file, blocks):
		self.annotation_file = annotation_file
		self.blocks = self.sort_blocks_by_start_coord(blocks)
		self.knockout_proportion_start = 0.5
		self.increased_expression_proportion_end= 0.3
		
		self.features = EMBLReader(self.annotation_file).read_annotation_features()
		
	def sort_blocks_by_start_coord(self, blocks):
		return sorted((b for b in blocks ), key=lambda x: x.start)
		
	def annotate_genes(self):
		genes = []
		for f in self.features:
			overlapping_blocks = self.blocks_overlapping_feature(f) 
			
			if len(overlapping_blocks) == 0:
				# no hits to any blocks so move to next feature
				continue

			g = Gene(f, overlapping_blocks)
			 
			# only consider block at a time
			for b in overlapping_blocks:
				if self.is_feature_contained_within_block(b, f):
					g.categories.append('total_inactivation')
				elif self.is_block_near_end_of_feature(b, f):
					if b.max_logfc > 0 :
						g.categories.append('increased_mutants_at_end_of_gene')
					else:
						g.categories.append('decreased_mutants_at_end_of_gene')
				elif self.is_block_near_start_of_feature(b,f):
					if b.max_logfc > 0 :
						g.categories.append('increased_mutants_at_start_of_gene')
					else:
						g.categories.append('decreased_mutants_at_start_of_gene')
			
			if len(g.categories) == 0:
				p = self.proportion_blocks_overlap_with_gene(f, overlapping_blocks)
				if p > 0.9:
					g.categories.append('over_90_perc_inactivation')
				elif p > 0.8:
					g.categories.append('over_80_perc_inactivation')	
				elif p > 0.7:
					g.categories.append('over_70_perc_inactivation')
				elif p > 0.6:
					g.categories.append('over_60_perc_inactivation')
				elif p > 0.5:
					g.categories.append('over_50_perc_inactivation')	
			
			if len(g.categories) == 0:
				g.categories.append('unclassified')
			genes.append(g)

		# intergenic test
		intergenic_blocks = [block for block in self.blocks if block.num_genes == 0]
		for block in intergenic_blocks:
			block.intergenic = True

		return genes 
		
	def proportion_blocks_overlap_with_gene(self,gene, blocks):
		base_coverage = 0
		for b in blocks:
			for b_index in range (b.start -1, b.end):
				if b_index >= gene.location.start and b_index < gene.location.end:
					base_coverage += 1
				
		gene_length = gene.location.end - gene.location.start
		return base_coverage/gene_length
			
		
	def blocks_overlapping_feature(self, feature):
		overlapping_blocks = []
		
		for block in self.blocks:

			if (block.start -1) > feature.location.end  or feature.location.start > block.end:
				continue
				
			# genes are big so you are bound to hit one. Smallest in ecoli is 45bp so half it.
			for i in range(block.start -1 , block.end, 22):
				if i in feature:
					overlapping_blocks.append(block)
					block.num_genes += 1
					break
		return overlapping_blocks
			
	def is_feature_contained_within_block(self, block, feature):
		if feature.location.start >= block.start -1 and feature.location.end <= block.end:
			return True
		return False
		
	def is_block_contained_within_feature(self, block, feature):
		if block.start -1 >= feature.location.start and block.end <= feature.location.end:
			return True
		return False
		
	def is_block_overlapping_feature_on_right(self, block, feature):
		if block.start -1  < feature.location.end and block.start -1 > feature.location.start and block.end > feature.location.end:
			return True
		return False
		
	def is_block_overlapping_feature_on_left(self, block, feature):	
		if block.end < feature.location.end and block.end > feature.location.start and block.start -1 < feature.location.start:
			return True
		return False
		
	def is_block_near_end_of_feature(self, block, feature):
		# forward 
		if feature.strand == 1 and block.direction in ['reverse', 'nodirection']:
			knock_out_start = feature.location.start + int(self.knockout_proportion_start * len(feature))
			if block.start -1  >= knock_out_start and block.start -1  < feature.location.end:
				return True
		# reverse
		if feature.strand == -1 and block.direction in ['forward', 'nodirection']:		
			knock_out_end = feature.location.end - int(self.knockout_proportion_start * len(feature))
			if block.end <= knock_out_end and block.end  > feature.location.start:
				return True
		
		return False
			
	def is_block_near_start_of_feature(self, block, feature):
		# forward
		if feature.strand == 1 and block.direction in ['forward','nodirection']:
			expression_end = feature.location.start +  int(self.increased_expression_proportion_end * len(feature))
			if block.end <= expression_end and block.end > feature.location.start:
				return True
		# reverse
		if feature.strand == -1 and block.direction in ['reverse', 'nodirection']:
			expression_end = feature.location.start +  int(self.increased_expression_proportion_end * len(feature))
			if block.end <= expression_end and block.end > feature.location.start:
				return True
				
		return False
		
		
		
		
		
		
		