import requests


proxies = {
    "http": "http://your-proxy-address:port",
    "https": "http://your-proxy-address:port",
}

def get_image_size(image_name, tag="latest"):
    url = f"https://hub.docker.com/v2/repositories/{image_name}/tags/{tag}/"
    try:
        response = requests.get(url, proxies=proxies, timeout=10)
        response.raise_for_status()
        data = response.json()
        images = data.get("images", [])
        if images:
            size_bytes = images[0].get("size", 0)
            return size_bytes
        else:
            return "No image size information found."

    except requests.exceptions.RequestException as e:
        return f"Error fetching image size: {e}"


if __name__ == "__main__":
    image = "library/ubuntu"
    tag = "latest"
    size = get_image_size(image, tag)
    if isinstance(size, int):
        print(f"The size of {image}:{tag} is {size / (1024 * 1024):.2f} MB.")
    else:
        print(size)
