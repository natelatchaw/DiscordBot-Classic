import io
from typing import Any, Callable

import torch
from context import Context
from discord import File, TextChannel
from PIL import Image


class GAN():

    def __init__(self, *args, **kwargs):
        pass

    async def anime(self, context: Context):
        """
        Applies AnimeGANv2 to an attached image.
        See https://github.com/bryandlee/animegan2-pytorch
        """

        for attachment in context.message.attachments:

            input_binary: io.BytesIO = io.BytesIO()
            file: File = await attachment.save(input_binary)
            input_binary.seek(0)
            source: Image = Image.open(input_binary).convert("RGB")

            model2 = torch.hub.load(
                "bryandlee/animegan2-pytorch:main",
                "generator",
                pretrained="face_paint_512_v2",
                #device="cuda",
                progress=False
            )

            face2paint: Callable[[Any, Image.Image], Image.Image] = torch.hub.load(
                "bryandlee/animegan2-pytorch:main", 
                "face2paint", 
                size=512
            )

            output: Image.Image = face2paint(model2, source)
            
            input_binary.close()

            extension: str = 'PNG'
            output_binary: io.BytesIO = io.BytesIO()
            output.save(output_binary, extension)
            output_binary.seek(0)
            channel: TextChannel = context.message.channel
            file: File = File(fp=output_binary, filename=f'output.{extension}')
            await channel.send(file=file)

            output_binary.close()
