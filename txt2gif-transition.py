import modules.scripts as scripts
import gradio as gr
import os
import uuid

from modules.processing import process_images, Processed, fix_seed
from modules.shared import opts, cmd_opts, state


def mapFromTo(x, a, b, c, d):
    y = (x-a)/(b-a)*(d-c)+c
    return round(y, 2)


def build_prompts(character_prompt, start_tag, end_tag, bias_min, bias_max, image_count):
    prompts = []

    image_count = int(image_count)

    for i in range(image_count):

        first_bias = mapFromTo((image_count-1-i) / (image_count-1), 0, 1, bias_min, bias_max)
        second_bias = mapFromTo(i / (image_count-1), 0, 1, bias_min, bias_max)

        prompts.append(f"({start_tag}:{first_bias}), ({end_tag}:{second_bias}), {character_prompt}, ")

    return prompts


def make_gif(frames, filename=None, gif_duration=100):
    if filename is None:
        filename = str(uuid.uuid4())

    outpath = "/output/txt2img-images/txt2gif-transition"
    if not os.path.exists(outpath):
        os.makedirs(outpath)

    first_frame, append_frames = frames[0], frames[1:]

    first_frame.save(f"{outpath}/{filename}.gif", format="GIF", append_images=append_frames, save_all=True, duration=gif_duration, loop=0)

    return first_frame


def main(p, start_tag, end_tag, bias_min, bias_max, image_count, gif_duration):
    character_prompt = p.prompt.strip().rstrip(',')
    frame_prompts = build_prompts(character_prompt, start_tag, end_tag, bias_min, bias_max, image_count)

    fix_seed(p)

    state.job_count = len(frame_prompts)

    imgs = []
    all_prompts = []
    infotexts = []

    for i in range(len(frame_prompts)):
        if state.interrupted:
            break

        p.prompt = frame_prompts[i]
        proc = process_images(p)

        if state.interrupted:
            break

        imgs += proc.images
        all_prompts += proc.all_prompts
        infotexts += proc.infotexts

    # remove pose images of ControlNet if present
    if len(frame_prompts) * 2 == len(imgs):
        del imgs[1::2]

    make_gif(imgs, gif_duration=gif_duration)

    return Processed(p, imgs, p.seed, "", all_prompts=all_prompts, infotexts=infotexts)


class Script(scripts.Script):
    is_txt2img = False

    # Function to set title
    def title(self):
        return "txt2gif-transition"

    def ui(self, is_img2img):
        with gr.Row():
            start_tag = gr.Textbox(label="Start tag", value="short hair")
            end_tag = gr.Textbox(label="End tag", value="long hair")
        with gr.Row():
            bias_min = gr.Number(label="Bias min", value=0.6)
            bias_max = gr.Number(label="Bias max", value=1.6)
        with gr.Row():
            image_count = gr.Number(label="Image count", value=12)
            gif_duration = gr.Number(label="Gif duration", value=100)
        return [start_tag, end_tag, bias_min, bias_max, image_count, gif_duration]

    # Function to show the script
    def show(self, is_img2img):
        return True

    # Function to run the script
    def run(self, p, start_tag, end_tag, bias_min, bias_max, image_count, gif_duration):
        # Make a process_images Object
        return main(p, start_tag, end_tag, bias_min, bias_max, image_count, gif_duration)
