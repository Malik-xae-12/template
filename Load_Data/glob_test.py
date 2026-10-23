import glob
import os

def search_in_path(path, pattern):
    """Search files/folders in a given path with a glob pattern."""
    return glob.glob(os.path.join(path, pattern))

if __name__ == "__main__":
    base_dir = r"E:\TC_BC\Reports"



    # 🔹 Example 2: find all PDFs for a URN across ALL dates
    urn = "296575"
    result = search_in_path(base_dir, f"*\\{urn}\\*.pdf")
    print(f"PDFs for URN {urn}:", result)

