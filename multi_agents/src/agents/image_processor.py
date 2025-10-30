import cv2
import pytesseract
from PIL import Image
import numpy as np
import os
import platform

class ImageProcessingAgent:
    def __init__(self):
        self.name = "Image Processing Agent"
        self.description = "Agent responsible for processing images and extracting text from nutritional labels"
        
        # Configure Tesseract path for Windows
        if platform.system() == "Windows":
            tesseract_paths = [
                os.environ.get('TESSERACT_PATH'),
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Users\kalyan.a\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
            ]
            
            for path in tesseract_paths:
                if path and os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    print(f"Using Tesseract from: {path}")
                    break

    def _preprocess_image_for_ocr(self, cv_image):
        """Apply a sequence of image-processing steps to improve OCR accuracy.

        Returns a single-channel (grayscale) OpenCV image suitable for tesseract.
        """
        # convert to gray
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

        # upscale / set DPI: enlarge small images so tesseract has more pixels for digits
        h, w = gray.shape[:2]
        scale = 1.0
        if w < 1000:
            scale = 2.0
        elif w < 1800:
            scale = 1.5
        if scale != 1.0:
            gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

        # denoise while keeping edges
        gray = cv2.bilateralFilter(gray, 9, 75, 75)

        # sharpen a little (unsharp mask)
        gaussian = cv2.GaussianBlur(gray, (0, 0), 3)
        alpha = 1.5
        gray = cv2.addWeighted(gray, alpha, gaussian, -0.5, 0)

        # adaptive thresholding to handle uneven lighting
        thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY, 11, 2)

        # morphological closing to join broken characters (use a small kernel)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        closed = cv2.morphologyEx(thr, cv2.MORPH_CLOSE, kernel)

        return closed

    def _merge_numeric_corrections(self, general_text: str, numeric_text: str) -> str:
        """Attempt to replace numeric tokens in general_text with those from numeric_text when they look more accurate."""
        import re
        nums_gen = re.findall(r"\d+[\d,\.]*%?", general_text)
        nums_num = re.findall(r"\d+[\d,\.]*%?", numeric_text)
        if not nums_num:
            return general_text

        # Simple strategy: if numeric_text has same number of numeric tokens, replace one-to-one
        if len(nums_gen) == len(nums_num):
            out = general_text
            for a, b in zip(nums_gen, nums_num):
                if a != b:
                    out = out.replace(a, b, 1)
            return out

        # fallback: prefer numeric_text if it looks more reasonable (has decimals)
        if any('.' in n for n in nums_num) and not any('.' in n for n in nums_gen):
            return numeric_text

        return general_text

    def _refine_numbers_with_bboxes(self, proc_image, merged_text: str) -> str:
        """Use pytesseract's image_to_data to get word boxes, and re-OCR numeric boxes with a tighter whitelist.

        Replace numeric tokens in merged_text when a higher-confidence numeric OCR is obtained.
        """
        import re
        data = pytesseract.image_to_data(proc_image, output_type=pytesseract.Output.DICT)
        n_boxes = len(data.get('text', []))
        corrected = merged_text

        for i in range(n_boxes):
            word = data['text'][i]
            conf_raw = data['conf'][i]
            if isinstance(conf_raw, int):
                conf = conf_raw
            elif isinstance(conf_raw, str):
                conf = int(conf_raw) if conf_raw.isdigit() else -1
            else:
                conf = -1
            if not word or not re.search(r'\d', word):
                continue
            # if confidence is low or word is large integer (possible missing dot), try numeric-only OCR on the box
            if word.isdigit() and len(word) >= 3:
                word_numeric = True
            else:
                word_numeric = False
            if conf < 85 or word_numeric:
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                margin = 4
                x0 = max(0, x - margin)
                y0 = max(0, y - margin)
                x1 = min(proc_image.shape[1], x + w + margin)
                y1 = min(proc_image.shape[0], y + h + margin)
                crop = proc_image[y0:y1, x0:x1]
                num_cfg = '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.,%'
                try:
                    new = pytesseract.image_to_string(crop, config=num_cfg).strip()
                except Exception:
                    new = word
                new = new.replace('\n', ' ').strip()
                # extract first numeric token
                m = re.search(r"\d+[\d,\.]*%?", new)
                if m:
                    new_num = m.group(0)
                    # replace the first occurrence of the old word in corrected text
                    corrected = re.sub(re.escape(word), new_num, corrected, count=1)

        return corrected

    def process_image(self, image_path):
        """
        Process the image and extract text using OCR
        """
        try:
            # Read image using PIL
            image = Image.open(image_path)
            
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Preprocessing and OCR with improved settings
            proc = self._preprocess_image_for_ocr(cv_image)

            # General OCR pass (for labels + numbers)
            general_config = '--oem 3 --psm 6'
            general_text = pytesseract.image_to_string(proc, config=general_config)

            # Numeric-focused pass: whitelist digits, dot and comma to improve numeric recognition
            numeric_config = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.,%'
            numeric_text = pytesseract.image_to_string(proc, config=numeric_config)

            # Try to intelligently merge numeric corrections from numeric_text into general_text
            merged_text = self._merge_numeric_corrections(general_text, numeric_text)

            # Additionally, perform a box-level numeric re-check for low-confidence words
            final_text = self._refine_numbers_with_bboxes(proc, merged_text)

            extracted_text = final_text
            
            return {
                "status": "success",
                "text": extracted_text,
                "error": None
            }
        except Exception as e:
            return {
                "status": "error",
                "text": None,
                "error": str(e)
            }