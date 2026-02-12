# *********************************************************************
# Image to PDF Converter                                              *
# ---------------------------------------------------------------------
# Description:                                                        *
#   GUI application that converts multiple images into a single PDF.  *
#   Each image becomes a separate PDF page.                           *
#                                                                     *
# Features:                                                           *
#   - Multiple image selection                                        *
#   - Add / Remove / Reorder images                                   *
#   - Auto page orientation (portrait / landscape)                    *
#   - EXIF rotation correction (phone photos supported)               *
#   - Transparency handling (RGBA → white background)                 *
#   - Save As dialog                                                  *
#   - Status updates and error handling                               *
#                                                                     *
# Developed by: Nikita Baiborodov                                     *
# *********************************************************************

# *********************************************************************
# Import Section                                                      *
# *********************************************************************
import tkinter as tk
from tkinter import filedialog, messagebox
from reportlab.pdfgen import canvas
from PIL import Image, ImageOps
import os

# *********************************************************************
# Main Converter Class                                                *
# *********************************************************************
class ImageToPDFConverter:

    # *****************************************************************
    # Constructor                                                     *
    # *****************************************************************
    def __init__(self, root: tk.Tk):
        # Store root window
        self.root = root

        # List storing FULL image paths
        self.image_paths: list[str] = []

        # UI variables
        self.output_pdf_name = tk.StringVar()
        self.status_text = tk.StringVar(value="Ready")

        # Listbox (shows filenames only)
        self.selected_images_listbox = tk.Listbox(
            root,
            selectmode=tk.EXTENDED,
            activestyle="dotbox"
        )

        # Build UI
        self.initialize_ui()

    # *****************************************************************
    # UI Initialization                                               *
    # *****************************************************************
    def initialize_ui(self) -> None:

        title_label = tk.Label(
            self.root,
            text="Image to PDF Converter",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=10)

        # *************************************************************
        # Top Buttons                                                 *
        # *************************************************************
        top_btn_frame = tk.Frame(self.root)
        top_btn_frame.pack(pady=(0, 10))

        select_images_button = tk.Button(
            top_btn_frame,
            text="Select Images",
            command=self.select_images
        )
        select_images_button.grid(row=0, column=0, padx=5)

        add_images_button = tk.Button(
            top_btn_frame,
            text="Add More",
            command=self.add_images
        )
        add_images_button.grid(row=0, column=1, padx=5)

        clear_button = tk.Button(
            top_btn_frame,
            text="Clear",
            command=self.clear_list
        )
        clear_button.grid(row=0, column=2, padx=5)

        # *************************************************************
        # Listbox + Scrollbar                                         *
        # *************************************************************
        list_frame = tk.Frame(self.root)
        list_frame.pack(pady=(0, 10), fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.selected_images_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.selected_images_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.selected_images_listbox.yview)

        # *************************************************************
        # Middle Control Buttons                                      *
        # *************************************************************
        mid_btn_frame = tk.Frame(self.root)
        mid_btn_frame.pack(pady=(0, 10))

        move_up_btn = tk.Button(mid_btn_frame, text="Move Up", command=self.move_up)
        move_up_btn.grid(row=0, column=0, padx=5)

        move_down_btn = tk.Button(mid_btn_frame, text="Move Down", command=self.move_down)
        move_down_btn.grid(row=0, column=1, padx=5)

        remove_selected_btn = tk.Button(
            mid_btn_frame,
            text="Remove Selected",
            command=self.remove_selected
        )
        remove_selected_btn.grid(row=0, column=2, padx=5)

        # *************************************************************
        # Output Name Section                                         *
        # *************************************************************
        label = tk.Label(self.root, text="Enter output PDF name (optional):")
        label.pack()

        pdf_name_entry = tk.Entry(
            self.root,
            textvariable=self.output_pdf_name,
            width=40,
            justify="center"
        )
        pdf_name_entry.pack(pady=(0, 10))

        # *************************************************************
        # Convert Button                                              *
        # *************************************************************
        convert_button = tk.Button(
            self.root,
            text="Convert to PDF",
            command=self.convert_images_to_pdf
        )
        convert_button.pack(pady=(10, 10))

        # Status label
        status_label = tk.Label(self.root, textvariable=self.status_text, anchor="w")
        status_label.pack(fill=tk.X, padx=10, pady=(0, 10))

    # *****************************************************************
    # File Selection Methods                                          *
    # *****************************************************************
    def select_images(self) -> None:
        """Replace list with newly selected images."""

        paths = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff")]
        )
        if not paths:
            return

        self.image_paths = list(paths)
        self.update_selected_images_listbox()
        self.status_text.set(f"Selected {len(self.image_paths)} image(s).")

    def add_images(self) -> None:
        """Append images to current list."""

        paths = filedialog.askopenfilenames(
            title="Add Images",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff")]
        )
        if not paths:
            return

        # Avoid duplicates while preserving order
        for p in paths:
            if p not in self.image_paths:
                self.image_paths.append(p)

        self.update_selected_images_listbox()
        self.status_text.set(f"Selected {len(self.image_paths)} image(s).")

    # *****************************************************************
    # Listbox Helpers                                                 *
    # *****************************************************************
    def update_selected_images_listbox(self) -> None:
        """Refresh listbox to display current filenames."""

        self.selected_images_listbox.delete(0, tk.END)
        for full_path in self.image_paths:
            filename = os.path.basename(full_path)
            self.selected_images_listbox.insert(tk.END, filename)

    def clear_list(self) -> None:
        """Clear all selected images."""

        self.image_paths.clear()
        self.update_selected_images_listbox()
        self.status_text.set("Cleared list.")

    def remove_selected(self) -> None:
        """Remove selected images from list."""

        selected = list(self.selected_images_listbox.curselection())
        if not selected:
            messagebox.showwarning("Nothing selected", "Select one or more images to remove.")
            return

        # Remove from bottom to top so indexes remain valid
        for idx in reversed(selected):
            del self.image_paths[idx]

        self.update_selected_images_listbox()
        self.status_text.set(f"Remaining {len(self.image_paths)} image(s).")

    def move_up(self) -> None:
        """Move selected items up in order."""

        selected = list(self.selected_images_listbox.curselection())
        if not selected:
            return
        if selected[0] == 0:
            return  # already at top

        # Move blocks upward preserving order
        for idx in selected:
            self.image_paths[idx - 1], self.image_paths[idx] = self.image_paths[idx], self.image_paths[idx - 1]

        self.update_selected_images_listbox()

        # Re-select moved items
        for idx in [i - 1 for i in selected]:
            self.selected_images_listbox.selection_set(idx)

    def move_down(self) -> None:
        """Move selected items down in order."""

        selected = list(self.selected_images_listbox.curselection())
        if not selected:
            return
        if selected[-1] == len(self.image_paths) - 1:
            return  # already at bottom

        # Move blocks downward (iterate reversed to avoid collisions)
        for idx in reversed(selected):
            self.image_paths[idx + 1], self.image_paths[idx] = self.image_paths[idx], self.image_paths[idx + 1]

        self.update_selected_images_listbox()

        # Re-select moved items
        for idx in [i + 1 for i in selected]:
            self.selected_images_listbox.selection_set(idx)

    # *****************************************************************
    # PDF Conversion Logic                                            *
    # *****************************************************************
    def convert_images_to_pdf(self) -> None:
        """Convert selected images into a single PDF."""

        if not self.image_paths:
            messagebox.showwarning("No images",
                                   "Please select at least one image.")
            return

        # Ask user where to save the PDF
        default_name = self.output_pdf_name.get().strip() or "output"

        save_path = filedialog.asksaveasfilename(
            title="Save PDF As",
            defaultextension=".pdf",
            initialfile=f"{default_name}.pdf",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not save_path:
            return

        try:
            # Create PDF canvas (pagesize will change per page if we do landscape/portrait)
            pdf = canvas.Canvas(save_path)

            total = len(self.image_paths)
            for i, image_path in enumerate(self.image_paths, start=1):
                self.status_text.set(f"Processing {i}/{total}: {os.path.basename(image_path)}")
                self.root.update_idletasks()

                # Open image safely
                with Image.open(image_path) as img:
                    # Fix phone-camera EXIF rotation
                    img = ImageOps.exif_transpose(img)

                    # Handle transparency by compositing onto white background
                    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                        rgba = img.convert("RGBA")
                        bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
                        img = Image.alpha_composite(bg, rgba).convert("RGB")
                    else:
                        img = img.convert("RGB")

                    # Auto page orientation based on image shape
                    portrait_size = (612, 792)   # Letter portrait
                    landscape_size = (792, 612)  # Letter landscape
                    page_w, page_h = portrait_size if img.height >= img.width else landscape_size

                    pdf.setPageSize((page_w, page_h))

                    # Margins & available area
                    margin = 36  # 0.5 inch
                    available_w = page_w - 2 * margin
                    available_h = page_h - 2 * margin

                    # Scale to fit while preserving aspect ratio
                    scale = min(available_w / img.width, available_h / img.height)
                    new_w = img.width * scale
                    new_h = img.height * scale

                    # Center on page
                    x = (page_w - new_w) / 2
                    y = (page_h - new_h) / 2

                    # Page background is already white; no need for a white rect.
                    pdf.drawInlineImage(img, x, y, width=new_w, height=new_h)
                    pdf.showPage()

            pdf.save()
            self.status_text.set(f"Done. Saved: {os.path.basename(save_path)}")
            messagebox.showinfo("Success", f"PDF created successfully:\n{save_path}")

        except Exception as ex:
            self.status_text.set("Error.")
            messagebox.showerror("Conversion failed", f"An error occurred:\n{ex}")

# *********************************************************************
# Application Entry Point                                             *
# *********************************************************************

def main() -> None:
    root = tk.Tk()
    root.title("Image to PDF")
    root.geometry("450x650")
    ImageToPDFConverter(root)
    root.mainloop()

# *********************************************************************
# Program Execution Guard                                             *
# *********************************************************************
if __name__ == "__main__":
    main()
