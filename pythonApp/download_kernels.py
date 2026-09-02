import os
import urllib.request

def download_file(url, save_path):
    print(f"Downloading {os.path.basename(url)}...")
    try:
        urllib.request.urlretrieve(url, save_path)
        print(f"Success! Saved to {save_path}")
    except Exception as e:
        print(f"Failed to download {url}. Error: {e}")

def main():
    kernel_dir = os.path.join(os.path.dirname(__file__), 'kernels')
    os.makedirs(kernel_dir, exist_ok=True)

    # NASA NAIF URLs
    lsk_url = "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/lsk/naif0012.tls"
    spk_url = "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de432s.bsp"

    lsk_path = os.path.join(kernel_dir, "naif0012.tls")
    spk_path = os.path.join(kernel_dir, "de432s.bsp")

    if not os.path.exists(lsk_path):
        download_file(lsk_url, lsk_path)
    else:
        print("Leapseconds kernel already exists.")

    if not os.path.exists(spk_path):
        download_file(spk_url, spk_path)
    else:
        print("Ephemeris kernel already exists.")

if __name__ == "__main__":
    main()