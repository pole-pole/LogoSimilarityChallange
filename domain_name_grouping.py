import csv
from jellyfish import jaro_winkler_similarity
from tldextract import extract
import time
import os


def read_domains_from_csv(filename, skip_header=True):
    """Read domains from CSV file's first column"""
    domains = []
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        if skip_header:
            next(reader, None)  # Skip header
        for row in reader:
            if row:
                domains.append(row[0])
    print(f"Read {len(domains)} domains from {filename}")
    return domains


def normalize_domain(domain):
    """Extract and normalize domain using tldextract with enhanced processing"""
    extracted = extract(domain)
    return ''.join(c for c in extracted.domain.lower() if c.isalnum())


def group_similar_domains(csv_file, threshold=0.82):
    """Group domains using Jaro-Winkler similarity with progress tracking"""
    domains = read_domains_from_csv(csv_file)
    normalized = [(dom, normalize_domain(dom)) for dom in domains]
    groups = []

    total_domains = len(normalized)
    start_time = time.time()

    for index, (domain, norm) in enumerate(normalized, 1):
        best_similarity = 0
        best_group = None

        for group in groups:
            base_norm = group['base']
            similarity = jaro_winkler_similarity(norm, base_norm)

            if similarity > best_similarity and similarity >= threshold:
                best_similarity = similarity
                best_group = group

        if best_group:
            best_group['members'].append(domain)
            common_prefix = os.path.commonprefix([best_group['base'], norm])
            if len(common_prefix) > len(best_group['base']):
                best_group['base'] = common_prefix
        else:
            groups.append({'base': norm, 'members': [domain]})

        if index % 10 == 0 or index == total_domains:  # Progress update every 10 domains
            elapsed_time = time.time() - start_time
            print(f"Processed {index}/{total_domains} domains. Elapsed time: {elapsed_time:.2f} seconds")

    print(f"Grouping complete. Total groups: {len(groups)}")
    return [g['members'] for g in groups]


def write_grouped_domains(groups, output_file):
    """Write grouped domains to CSV with group names"""
    with open(output_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Domain', 'Group'])
        for i, group in enumerate(groups, 1):
            group_name = f'domain_group_{i}'
            for domain in group:
                writer.writerow([domain, group_name])
    print(f"Results written to {output_file}")


# Example usage
if __name__ == "__main__":
    input_csv = 'url_list_deduplicated_orig.csv'
    output_csv = 'domain_groups.csv'

    print("Starting domain grouping process...")
    domain_groups = group_similar_domains(input_csv)
    write_grouped_domains(domain_groups, output_csv)
    print("Process completed successfully.")
