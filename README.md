# TrafficEye AI – Python Example

Simple Python client and examples for the [TrafficEye](https://trafficeye.ai) REST API:
**license plate recognition (ANPR/ALPR)**, **vehicle detection**, **OCR** and
**vehicle make, model, color and category recognition (MMR)** from a single image.

Sign up, copy your API key, run one command.

## Why TrafficEye

Built on [Eyedea](https://www.eyedea.ai) recognition technology, developed since 2006:

- **Accurate plate reading:** over 99% full-plate accuracy in image-optimized installations, with plate text, country/state and plate type. Covers Europe, the Americas, Africa, Asia, Oceania and the Middle East, day and night. [Learn more about ANPR](https://www.eyedea.ai/products/number-plate-reading-anpr)
- **Detailed vehicle recognition:** 374 makes, 3,085 models and 8,030 generations, plus color, category and visual tags. Over 99% make and over 98% model accuracy. Works without a visible plate. [Learn more about MMR](https://www.eyedea.ai/products/make-and-model-recognition-mmr)

*Accuracy depends on image quality, camera setup and region.*

## Quick start

**1. Get an API key**

Register at [trafficeye.ai](https://trafficeye.ai) and copy your key from
[trafficeye.ai/user/licenses](https://trafficeye.ai/user/licenses).

**2. Clone and install**

```bash
git clone https://github.com/Eyedea-Recognition/trafficeye-ai-python.git
cd trafficeye-ai-python

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**3. Set your API key**

```bash
cp .env.example .env             # Windows: copy .env.example .env
```

Open `.env` and replace `your_api_key_here` with your key.
(Alternatively: `export TRAFFICEYE_API_KEY=...`)

**4. Run**

```bash
python example.py
```

This analyzes the two bundled images in [`images/`](images) and prints the recognized
plate, make, model, color and category of every vehicle:

```text
images/example_image_01.jpg
  Vehicle 1: plate=4AU2222 | Porsche 911 | color=BLUE | category=CAR
```

## Use your own images

```bash
python example.py photo.jpg
python example.py https://example.com/car.jpg
python example.py --json photo.jpg      # full JSON response
```

## Use it in your code

```python
from trafficeye import TrafficEyeClient

client = TrafficEyeClient("YOUR_API_KEY")

result = client.recognition("images/example_image_01.jpg")

for combination in result["data"]["combinations"]:
    for road_user in combination["roadUsers"]:
        for plate in road_user.get("plates", []):
            print(plate["text"]["value"], plate["text"]["score"])
        mmr = road_user.get("mmr", {})
        print(mmr.get("make", {}).get("value"), mmr.get("model", {}).get("value"))
```

Choose what the API should do with the `tasks` parameter:

```python
client.recognition("car.jpg", tasks=["DETECTION", "OCR"])   # plates only, no make/model
```

| Task        | Result                                                    |
|-------------|-----------------------------------------------------------|
| `DETECTION` | Vehicles, license plates and windshields with positions   |
| `OCR`       | License plate text and plate type                         |
| `MMR`       | Vehicle make, model, generation, color, category and tags |

Requesting only `DETECTION` and `OCR` costs fewer credits than adding `MMR`.

Errors (invalid API key, unreachable image URL, server errors) raise `trafficeye.TrafficEyeError`.

## Documentation

Full API reference, response format and all parameters:
[trafficeye.ai](https://trafficeye.ai) (API documentation).

## Requirements

- Python 3.8+
- A TrafficEye API key

## License

[MIT](LICENSE)
