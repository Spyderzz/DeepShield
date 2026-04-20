Here is a full, detailed context summary structured specifically for an AI agent like ClaudeCode to instantly understand our architectural changes, codebase state, and exact progression:

***

### 📝 Context Summary: DeepShield Phase 11.1 Updates & Training Architecture

**1. OS Compatibility & Orchestration Fixes**
*   **Issue:** The user is operating strictly on Windows without WSL, causing the original UNIX bash script (`datasets/procure_all.sh`) to fail.
*   **Action:** Translated the pipeline into a native Windows PowerShell script (`backend/training/datasets/procure_all.ps1`) to handle the directory setup and execute the python modules. 
*   **Action:** Created the `~/.kaggle` directory locally to resolve API configuration blockers.

**2. Architecture Pivot: Bypassing Local Hardware Limits**
*   **Constraint:** The user lacks a local discrete GPU and is limited to ~50GB of free space on their D: Drive, making local training of a ConvNeXt/CNN architecture practically impossible.
*   **Pivot:** Shifted model training entirely to **Google Colab (T4 GPUs)**. The strategy is to train purely in the cloud, export the lightweight `.safetensors` model, and run *only* the Inference locally for the Web Backend.
*   **Model Upgrade:** Upgraded from CNNs to **Vision Transformers (ViT)** using Transfer Learning via HuggingFace (`google/vit-base-patch16-224-in21k`). This provides State-of-the-Art accuracy for detecting deepfake blending artifacts.

**3. The Google Colab Web Pipeline**
*   **Action:** Wrote a local generator script (`generate_colab_nb.py`) that outputs a ready-to-run Jupyter Notebook (`Colab_ViT_Training.ipynb`).
*   **Pipeline specifics inside Colab:**
    *   **Download:** Drops the massive `raw` uncompressed format for the `c40` (high-compression) format to fit in Colab RAM. Switched the connection from the primary TUM `canis` server (which was down/refusing connections) to the backup `kaldir` EU2 server. Fixed a naming convention bug where `original` youtube videos (e.g. `000.mp4`) were mistakenly failing due to being queried as pair strings (`000_003.mp4`).
    *   **Extraction:** Uses `cv2` to extract static frames from `.mp4` into binary `real/` and `fake/` folders.
    *   **Pre-Processing:** Drops the supplementary/complex Google DFD Actor dataset entirely. Strict focus on the core 5 components of the FF++ benchmark (YouTube Original, Deepfakes, Face2Face, FaceSwap, NeuralTextures).
    *   **Training Loop:** Implemented a HuggingFace `Trainer` loop. Fixed strict compatibility errors for Transformers 4.40+ (renamed `evaluation_strategy` to `eval_strategy` and removed deprecated `tokenizer` kwargs for `ViTImageProcessor`). 
*   **Result:** A test run of 50-videos / 3-epochs was flawlessly executed on Colab. The model learned to classify real vs fake and successfully saved the export weights (`deepshield_vit_model`).

**4. Flickr Artifact Purge**
*   **Constraint:** Corporate policies block the user from creating a free Flickr API key. 
*   **Action:** Completely scrubbed the Flickr CC "anchor set" concept from the entire repository to remove API bottlenecks and simplify the scope.
*   **Files Cleaned:** 
    *   Deleted `download_flickr_cc.py`.
    *   Removed `flickr` paths and array logic from `build_manifest.py` and `__init__.py`.
    *   Removed execution statements from `procure_all.ps1` and `procure_all.sh`.
    *   Stripped all conceptual references, EULA warnings, and anchor-gate logic from `docs/datasets.md` and `BUILD_PLAN2.md`. 

**Current State for Next Steps:**
The Cloud Training pipeline is officially tested and functional. The user is now proceeding to train the model on a larger batch (`-n 300`, 15 Epochs) in Colab to maximize accuracy. Once finished, they will download the final ViT weights to their local `minor2` env to begin coding the Web Application Backend / Inference API.

*** 
*(You can just hit copy on the block above and paste it right into Claude!)*