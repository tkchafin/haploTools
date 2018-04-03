#!/usr/bin/python

import re
import sys
import os
import getopt
import Bio
import alignment_tools as aln
from Bio import AlignIO

def main():
	params = parseArgs()

	#Now, get the alignment from the FASTA file (as another dict)
	if params.fasta:
		pop_assign = dict()
		seqs = dict()
		#print('Reading alignment from FASTA...')
		for f in read_fasta(params.fasta):
			seqs[f[0]] = f[1]
			
		#parse popmap file for dictionary of sample assignments
		if params.popmap:
			#print("Parsing popmap file...")
			pop_assign = parsePopmap(params.popmap)
			
		#Make dict of lists representing populations 
		pops = dict()
		pops["TOTAL"]=(list(seqs.values()))
		if params.popmap:
			for samp in seqs:
				if samp in pop_assign:
					if pop_assign[samp] in pops:
						pops[pop_assign[samp]].append(seqs[samp])
					else:
						t = list()
						t.append(seqs[samp])
						#print("adding", pop_assign[samp],"to dict")
						pops[pop_assign[samp]]=t
				else:
					print("Warning: Sample %s isn't in popmap."%samp)
					
		#Grab table contents
		hapTotals = dict()
		for hap in pops["TOTAL"]:
			hapTotals[hap] = dict()
		#Now, parse pops to get frequencies 
		for pop in pops:
			counts = dict()
			total = 0
			for hap in pops[pop]:
				total = total + 1
				if hap in counts:
					counts[hap] = counts[hap]+1
				else:
					counts[hap]=1
			print("Haplotype frequencies for pop %s:"%pop)
			for key in counts:
				f = float(counts[key])/float(total)
				print("%s:%s"%(key,("{0:.4f}".format(f))))
				hapTotals[key][pop] = f
			print()
			
		#Write table 
		with open(params.out, 'w') as fh:
			try:
				popOrder = pops.keys()
				header = "Haplotype"
				for p in popOrder:
					header = header + "\t" + str(p)
				header = header + "\n"
				fh.write(header)
				
				#Print haplotype line 
				for hap in hapTotals:
					hapLine = str(hap)
					for p in popOrder:
						if p in hapTotals[hap]:
							hapLine = hapLine + "\t" + str(("{0:.4f}".format(hapTotals[hap][p])))
						else:
							hapLine = hapLine + "\t" + str(0.0000)
					hapLine = hapLine + "\n"
					fh.write(hapLine)
			except IOError: 
				print("Could not read file ",nex)
				sys.exit(1)
			finally:
				fh.close()



		
	else:
		print("No input provided")
		sys.exit(1)



#Read genome as FASTA. FASTA header will be used
#This is a generator function
#Doesn't matter if sequences are interleaved or not.
def read_fasta(fas):

	if os.path.exists(fas):
		with open(fas, 'r') as fh:
			try:
				contig = ""
				seq = ""
				for line in fh:
					line = line.strip()
					if not line:
						continue
					#print(line)
					if line[0] == ">": #Found a header line
						#If we already loaded a contig, yield that contig and
						#start loading a new one
						if contig:
							yield([contig,seq]) #yield
							contig = "" #reset contig and seq
							seq = ""
						split_line = line.split()
						contig = (split_line[0].replace(">",""))
					else:
						seq += line
				#Iyield last sequence, if it has both a header and sequence
				if contig and seq:
					yield([contig,seq])
			except IOError: 
				print("Could not read file ",fas)
				sys.exit(1)
			finally:
				fh.close()
	else:
		raise FileNotFoundError("File %s not found!"%fas)


#Function to check that list of sample names and popmap entries match
def validatePopmap(samples, popmap):
	print(samples)
	print(popmap)
	for samp in samples:
		if samp in popmap:
			print("Warning: Sample %s not found in popmap!"%samp)
	for key in popmap:
		if key not in samples:
			print("Warning: Sample %s found in popmap has no data!"%key)

#function reads a tab-delimited popmap file and return dictionary of assignments 
def parsePopmap(popmap):

	ret = dict()
	if os.path.exists(popmap):
		with open(popmap, 'r') as fh:
			try:
				contig = ""
				seq = ""
				for line in fh:
					line = line.strip()
					if not line:
						continue
					else:
						stuff = line.split()
						ret[stuff[0]] = stuff[1]
				return(ret)
			except IOError: 
				print("Could not read file ",popmap)
				sys.exit(1)
			finally:
				fh.close()
	else:
		raise FileNotFoundError("File %s not found!"%popmap)


#Object to parse command-line arguments
class parseArgs():
	def __init__(self):
		#Define options
		try:
			options, remainder = getopt.getopt(sys.argv[1:], 'p:o:hf:d', \
			["popmap=","out=","help","fasta=","dip"])
		except getopt.GetoptError as err:
			print(err)
			self.display_help("\nExiting because getopt returned non-zero exit status.")
		#Default values for params
		#Input params
		self.popmap=None
		self.out=None
		self.fasta=None
		self.dip=False

		#First pass to see if help menu was called
		for o, a in options:
			if o in ("-h", "-help", "--help"):
				self.display_help("Exiting because help menu was called.")

		#Second pass to set all args.
		for opt, arg_raw in options:
			arg = arg_raw.replace(" ","")
			arg = arg.strip()
			opt = opt.replace("-","")
			#print(opt,arg)
			if opt in ('p', 'popmap'):
				self.popmap= arg
			elif opt in ('h', 'help'):
				pass
			elif opt in ('o','out'):
				self.out = arg
			elif opt in ("f","fasta"):
				self.fasta = arg
			elif opt in ("d","dip"):
				self.dip=True
			else:
				assert False, "Unhandled option %r"%opt

		#Check manditory options are set
		if not self.fasta:
			self.display_help("Error: Missing required input file (-f,--fasta).")

		if self.out:
			self.out = self.out + "_freq.tsv"
		else:
			self.out = "out_freq.tsv"


	def display_help(self, message=None):
		if message is not None:
			print()
			print (message)
		print ("\nhapFrequency.py\n")
		print ("Contact:Tyler K. Chafin, University of Arkansas,tkchafin@uark.edu")
		print ("\nUsage: ", sys.argv[0], "-f </path/to/fasta>  <-o out_prefix> <-p /path/to/popmap>\n")
		print ("Description: Extracts haplotype frequencies from a FASTA file")

		print("""
	Arguments:
		-f,--fasta	: Path to FASTA file. If diplotypes, separate with _A and _B
		-o,--out	: Prefix for output file <default = ./out>
		-p,--popmap	: Path to tab-delimited population map, if you want to group
		-h,--help	: Displays help menu
		""")
		print()
		sys.exit()


#Function to check if a file path is valid
def fileCheck(f):
	return (os.path.isfile(f))


#Call main function
if __name__ == '__main__':
    main()
