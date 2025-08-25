import html
import re


class BBCodeParser:
    """A simple BBCode to HTML parser for Steam Workshop descriptions."""

    def __init__(self):

        self.patterns = [
            (r'\[h1\](.*?)\[/h1\]', r'<h1>\1</h1>'), (r'\[h2\](.*?)\[/h2\]', r'<h2>\1</h2>'),
            (r'\[h3\](.*?)\[/h3\]', r'<h3>\1</h3>'), (r'\[h4\](.*?)\[/h4\]', r'<h4>\1</h4>'),
            (r'\[h5\](.*?)\[/h5\]', r'<h5>\1</h5>'), (r'\[h6\](.*?)\[/h6\]', r'<h6>\1</h6>'),

            (r'\[hr\]', r'<hr>'),

            (r'\[b\](.*?)\[/b\]', r'<strong>\1</strong>'), (r'\[i\](.*?)\[/i\]', r'<em>\1</em>'),
            (r'\[u\](.*?)\[/u\]', r'<u>\1</u>'), (r'\[s\](.*?)\[/s\]', r'<s>\1</s>'),
            (r'\[sup\](.*?)\[/sup\]', r'<sup>\1</sup>'), (r'\[sub\](.*?)\[/sub\]', r'<sub>\1</sub>'),

            (r'\[center\](.*?)\[/center\]', r'<div style="text-align: center;">\1</div>'),
            (r'\[left\](.*?)\[/left\]', r'<div style="text-align: left;">\1</div>'),
            (r'\[right\](.*?)\[/right\]', r'<div style="text-align: right;">\1</div>'),
            (r'\[justify\](.*?)\[/justify\]', r'<div style="text-align: justify;">\1</div>'),

            (r'\[url=(.*?)\](.*?)\[/url\]', r'<a href="\1" target="_blank">\2</a>'),
            (r'\[url\](.*?)\[/url\]', r'<a href="\1" target="_blank">\1</a>'),

            (r'\[img\](.*?)\[/img\]', r'<img src="\1" style="max-width: 100%; height: auto;" alt="Image">'),
            (r'\[img=(.*?)x(.*?)\](.*?)\[/img\]',
             r'<img src="\3" width="\1" height="\2" style="max-width: 100%; height: auto;" alt="Image">'),

            (r'\[code\](.*?)\[/code\]',
             r'<pre style="background: #f0f0f0; padding: 10px; border-radius: 4px; overflow-x: auto; border: 1px solid #ddd;"><code>\1</code></pre>'),
            (r'\[code=(.*?)\](.*?)\[/code\]',
             r'<pre style="background: #f0f0f0; padding: 10px; border-radius: 4px; overflow-x: auto; border: 1px solid #ddd;"><code class="language-\1">\2</code></pre>'),

            (r'\[c\](.*?)\[/c\]',
             r'<code style="background: #f0f0f0; padding: 2px 4px; border-radius: 2px; border: 1px solid #ddd;">\1</code>'),

            (r'\[list\](.*?)\[/list\]', r'<ul>\1</ul>'), (r'\[ul\](.*?)\[/ul\]', r'<ul>\1</ul>'),
            (r'\[list=1\](.*?)\[/list\]', r'<ol>\1</ol>'), (r'\[ol\](.*?)\[/ol\]', r'<ol>\1</ol>'),
            (r'\[list=a\](.*?)\[/list\]', r'<ol style="list-style-type: lower-alpha;">\1</ol>'),
            (r'\[list=A\](.*?)\[/list\]', r'<ol style="list-style-type: upper-alpha;">\1</ol>'),
            (r'\[list=i\](.*?)\[/list\]', r'<ol style="list-style-type: lower-roman;">\1</ol>'),
            (r'\[list=I\](.*?)\[/list\]', r'<ol style="list-style-type: upper-roman;">\1</ol>'),

            (r'\[\*\](.*?)(?=\[\*\]|\[/(?:list|ul|ol)\])', r'<li>\1</li>'), (r'\[li\](.*?)\[/li\]', r'<li>\1</li>'),

            (r'\[table\](.*?)\[/table\]', r'<table style="border-collapse: collapse; width: 100%;">\1</table>'),
            (r'\[tr\](.*?)\[/tr\]', r'<tr>\1</tr>'),
            (r'\[td\](.*?)\[/td\]', r'<td style="border: 1px solid #ddd; padding: 8px;">\1</td>'),
            (r'\[th\](.*?)\[/th\]',
             r'<th style="border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2; font-weight: bold;">\1</th>'),

            (r'\[quote\](.*?)\[/quote\]',
             r'<blockquote style="border-left: 4px solid #ccc; margin: 10px 0; padding: 10px; background: #f9f9f9; border-radius: 4px;">\1</blockquote>'),
            (r'\[quote=(.*?)\](.*?)\[/quote\]',
             r'<blockquote style="border-left: 4px solid #ccc; margin: 10px 0; padding: 10px; background: #f9f9f9; border-radius: 4px;"><strong>\1 said:</strong><br>\2</blockquote>'),

            (r'\[spoiler\](.*?)\[/spoiler\]',
             r'<details style="margin: 5px 0;"><summary style="cursor: pointer; padding: 5px; background: #f0f0f0; border-radius: 4px;">Spoiler</summary><div style="padding: 10px; border: 1px solid #ddd; margin-top: 5px; border-radius: 4px;">\1</div></details>'),
            (r'\[spoiler=(.*?)\](.*?)\[/spoiler\]',
             r'<details style="margin: 5px 0;"><summary style="cursor: pointer; padding: 5px; background: #f0f0f0; border-radius: 4px;">\1</summary><div style="padding: 10px; border: 1px solid #ddd; margin-top: 5px; border-radius: 4px;">\2</div></details>'),

            (r'\[size=(\d+)\](.*?)\[/size\]', self._convert_size),
            (r'\[color=(.*?)\](.*?)\[/color\]', r'<span style="color: \1;">\2</span>'),
            (r'\[font=(.*?)\](.*?)\[/font\]', r'<span style="font-family: \1;">\2</span>'),

            (r'\[youtube\](.*?)\[/youtube\]',
             r'<iframe width="560" height="315" src="https://www.youtube.com/embed/\1" frameborder="0" allowfullscreen></iframe>'),
            (r'\[video\](.*?)\[/video\]',
             r'<video controls style="max-width: 100%;"><source src="\1" type="video/mp4">Your browser does not support the video tag.</video>'),
            (r'\[audio\](.*?)\[/audio\]',
             r'<audio controls><source src="\1" type="audio/mpeg">Your browser does not support the audio element.</audio>'),

            (r'\[email\](.*?)\[/email\]', r'<a href="mailto:\1">\1</a>'),
            (r'\[email=(.*?)\](.*?)\[/email\]', r'<a href="mailto:\1">\2</a>'),

            (r'\[url=https://steamcommunity\.com/profiles/(\d+)\](.*?)\[/url\]',
             r'<a href="https://steamcommunity.com/profiles/\1" target="_blank">\2</a>'),
            (r'\[url=https://steamcommunity\.com/sharedfiles/filedetails/\?id=(\d+)\](.*?)\[/url\]',
             r'<a href="https://steamcommunity.com/sharedfiles/filedetails/?id=\1" target="_blank">\2</a>'), ]

    def _convert_size(self, match):
        """Convert BBCode size to approximate CSS font-size."""
        size = int(match.group(1))

        css_size = max(0.6, min(2.0, size / 5.0))
        return f'<span style="font-size: {css_size}em;">{match.group(2)}</span>'

    def parse(self, bbcode_text):
        """Convert BBCode text to HTML."""
        if not bbcode_text:
            return "<p>No description available.</p>"

        html_text = html.escape(bbcode_text)

        for pattern, replacement in self.patterns:
            if callable(replacement):
                html_text = re.sub(pattern, replacement, html_text, flags=re.DOTALL | re.IGNORECASE)
            else:
                html_text = re.sub(pattern, replacement, html_text, flags=re.DOTALL | re.IGNORECASE)

        html_text = re.sub(r'\r?\n', '<br>', html_text)

        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 10px;
                    line-height: 1.4;
                    word-wrap: break-word;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    margin-top: 20px;
                    margin-bottom: 10px;
                    color: #333;
                }}
                h1 {{ font-size: 2em; }}
                h2 {{ font-size: 1.8em; }}
                h3 {{ font-size: 1.6em; }}
                h4 {{ font-size: 1.4em; }}
                h5 {{ font-size: 1.2em; }}
                h6 {{ font-size: 1em; }}
                hr {{
                    border: none;
                    border-top: 1px solid #ccc;
                    margin: 20px 0;
                }}
                ul, ol {{
                    margin: 10px 0;
                    padding-left: 30px;
                }}
                li {{
                    margin: 5px 0;
                }}
                table {{
                    margin: 10px 0;
                }}
                a {{
                    color: #0066cc;
                    text-decoration: underline;
                }}
                a:hover {{
                    text-decoration: none;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                    display: block;
                    margin: 5px 0;
                }}
                pre {{
                    white-space: pre-wrap;
                    word-wrap: break-word;
                }}
                blockquote {{
                    margin-left: 0;
                }}
                video, audio, iframe {{
                    max-width: 100%;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            {html_text}
        </body>
        </html>
        """

        return full_html
