import traceback
from graph_builder import extract_and_store_graph
from utils import get_files_to_index

try:
    files = get_files_to_index('data/repos/NikhilJaiswal-79-safestep-b6eb8840')
    extract_and_store_graph('test_safestep_subset', files[30:40])
    print('Success')
except Exception as e:
    traceback.print_exc()
