import csv

def generator_to_csv(generator, header, filename, delimeter=',', quotechar='"'):
    with open(filename, 'w') as csv_file:
        csv_writer = csv.writer(csv_file,
                                delimiter=delimeter, 
                                quotechar=quotechar)
        csv_writer.writerow(header)
        csv_writer.writerows(generator)
