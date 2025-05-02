#!/usr/bin/env ruby
# Script to help manage tags in the LRD bibliography
# This script can be used to find inconsistencies between tag definitions and usage

require 'yaml'
require 'bibtex'
require 'fileutils'
require 'colorize'

# Paths
DATA_DIR = File.join(File.dirname(__FILE__), '..', '_data')
LIBRARY_DIR = File.join(File.dirname(__FILE__), '..', '..', 'library')
TAG_FILE = File.join(DATA_DIR, 'lrd_tags.yml')
BIB_FILE = File.join(LIBRARY_DIR, 'aslrd.bib')

# Ensure directories exist
FileUtils.mkdir_p(DATA_DIR) unless Dir.exist?(DATA_DIR)

# Load tag definitions
def load_tags
  if File.exist?(TAG_FILE)
    data = YAML.load_file(TAG_FILE)
    tags = data['tags'].map { |t| t['tag'].downcase }
    return tags
  else
    puts "Tag file not found: #{TAG_FILE}".red
    return []
  end
end

# Load BibTeX entries and extract used tags
def load_bib_tags
  if File.exist?(BIB_FILE)
    bib = BibTeX.open(BIB_FILE)
    used_tags = []
    
    bib.each do |entry|
      next unless entry.respond_to?(:lrdKeys) && entry.lrdKeys
      
      # Extract tags from lrdKeys field
      tags = entry.lrdKeys.to_s.split(',').map(&:strip).map(&:downcase)
      used_tags.concat(tags)
    end
    
    return used_tags.uniq
  else
    puts "BibTeX file not found: #{BIB_FILE}".red
    return []
  end
end

# Find tags used in BibTeX but not defined in YAML
def find_undefined_tags(defined_tags, used_tags)
  used_tags - defined_tags
end

# Main execution
puts "LRD Tag Manager".blue
puts "===============".blue

defined_tags = load_tags
used_tags = load_bib_tags

puts "\nDefined tags (#{defined_tags.count}):".green
defined_tags.sort.each { |tag| puts "  - #{tag}" }

puts "\nUnique tags used in BibTeX (#{used_tags.count}):".green
used_tags.sort.each { |tag| puts "  - #{tag}" }

undefined_tags = find_undefined_tags(defined_tags, used_tags)
if undefined_tags.any?
  puts "\nWarning: Tags used in BibTeX but not defined in YAML:".yellow
  undefined_tags.sort.each { |tag| puts "  - #{tag}" }
  
  puts "\nConsider adding these tags to #{TAG_FILE}".yellow
else
  puts "\nAll tags are properly defined! ✓".green
end 