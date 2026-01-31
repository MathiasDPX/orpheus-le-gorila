from bs4 import BeautifulSoup

def shorten_text(text):
    """Cut the text to 200 chars, remove the last word and replace by '...' (if needed)"""
    if len(text) < 200:
        return text
    
    text = text[:200]
    text = " ".join(text.split(" ")[:-1])
    text = text + "..."
    
    return text

def html_to_mrkdwn(html:str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    
    # Line breaks
    for br in soup.find_all("br"):
        br.replace_with("\n")
        
    # Bold
    for tag in soup.find_all(["strong", "b"]):
        tag.replace_with(f"*{tag.get_text()}*")
        
    # Italic
    for tag in soup.find_all(["em", "i"]):
        tag.replace_with(f"_{tag.get_text()}_")
    
    # Links    
    for tag in soup.find_all("a", href=True):
        text = tag.get_text()
        href = tag["href"]
        tag.replace_with(f"<{href}|{text}>")
        
    # Blockquotes
    for bq in soup.find_all("blockquote"):
        lines = bq.get_text().splitlines()
        quoted = "\n".join(f"> {line}" for line in lines if line.strip())
        bq.replace_with(quoted)
        
    return soup.get_text()

if __name__ == "__main__":
    print("HTML to Mrkdwn")
    print("---")
    print(html_to_mrkdwn('<p>It was <b>fun</b> to <em>watch</em></p>\n\n<blockquote>67</blockquote>\nthis made me laugh\n\n<a href="https://www.youtube.com/watch?v=dQw4w9WgXcQ">Rickroll</a>'))
    
    print("---\n" + shorten_text("Firstly, great performances from the cast, especially Jesse Plemons. Emma definitely deserved her Oscar nomination for this film and Aidan was amazing. I thought it was a great commentary on conspiracy theorists, it was actually a bit fun but also extremely sad at the same time. Teddy and Don’s relationship was wonderful but also heartbreaking. Teddy going deeper and deeper into this pit, as Michelle said, dragging Don with him. Not seeing how he was hurting his own cousin. I quite liked the twist ending too, and the end sequence was simple but brilliant. Overall a great film that I definitely recommend."))