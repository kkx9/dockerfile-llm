import requests
import json


def fetch_image_manifest(image_name, repo="library", proxy=None):
    res = []
    url = f"https://hub.docker.com/v2/repositories/{repo}/{image_name}/tags"
    while url:
        try:
            response = requests.get(url, proxies=proxy, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "results" in data and data["results"]:
                for result in data["results"]:
                    if "images" in result and result["images"]:
                        for image in result["images"]:
                            if "architecture" in image and image["architecture"] == "amd64":
                                image["name"] = f"{image_name}:{result['name']}"
                                res.append(image)
                                break
            url = data.get("next")
        except Exception as e:
            print(e)
            break
    return res


def save_to_jsonl(data_list, output_file):
    with open(output_file, 'w', encoding='utf-8') as file:
        for entry in data_list:
            json_line = json.dumps(entry, ensure_ascii=False)
            file.write(json_line + '\n')


def fetch_official_images(proxy=None):
    url = "https://hub.docker.com/v2/repositories/library/?page=1"
    images = []

    while url:
        try:
            response = requests.get(url, proxies=proxy, timeout=10)
            response.raise_for_status()
            data = response.json()
            images.extend([repo["name"] for repo in data.get("results", [])])
            url = data.get("next")
        except Exception as e:
            print(f"Error fetching official images: {e}")
            break

    return images


def main():
    proxy = {
        "http": "http://127.0.0.1:10809",
        "https": "http://127.0.0.1:10809"
    }
    images = fetch_official_images(proxy)
    print(images)
    results = []
    for image in images:
        print(f"Fetching manifest for {image}...")
        result = fetch_image_manifest(image, proxy=proxy)
        results.extend(result)

    output_file = "office_image_manifest.jsonl"
    save_to_jsonl(results, output_file)
    print(f"Image manifest saved to {output_file}")


if __name__ == "__main__":
    main()
