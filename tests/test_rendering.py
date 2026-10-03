from datetime import datetime


def test_hugo_homepage_resolves_local_image_frame_background(built_site):
    homepage = (built_site / "index.html").read_text(encoding="utf-8")

    assert "background-image: url('/posts/" in homepage
    assert "background-image: url('https://bear-images.sfo2.cdn.digitaloceanspaces.com/" not in homepage


def test_hugo_post_page_resolves_local_image_frame_background(built_site):
    destination = built_site
    post_page = (
        destination / "posts" / "2026" / "01" / "05" / "a-cabeca-do-santo" / "index.html"
    ).read_text(encoding="utf-8")

    assert "background-image: url('/posts/2026/01/05/a-cabeca-do-santo/a-cabeca-do-santo.webp')" in post_page
    assert 'data-src="/posts/2026/01/05/a-cabeca-do-santo/a-cabeca-do-santo.webp"' in post_page
    assert "background-image: url('https://bear-images.sfo2.cdn.digitaloceanspaces.com/" not in post_page


def test_hugo_tag_links_resolve_to_generated_term_pages(built_site):
    destination = built_site
    tag_page = destination / "tags" / "filmes" / "index.html"
    post_page = (
        destination / "posts" / "2025" / "03" / "04" / "flow" / "index.html"
    ).read_text(encoding="utf-8")

    assert tag_page.is_file()
    assert '<h3><a href="/tags/filmes/">#filmes</a></h3>' in post_page


def test_hugo_post_page_loads_goatcounter_and_tracks_contact_email(built_site):
    destination = built_site
    post_page = (
        destination / "posts" / "2025" / "03" / "04" / "flow" / "index.html"
    ).read_text(encoding="utf-8")

    assert 'src="https://gc.zgo.at/count.js"' in post_page
    assert 'data-goatcounter="https://blog-de-teste.goatcounter.com/count"' in post_page
    assert 'href="mailto:leitor@example.com"' in post_page
    assert 'data-goatcounter-click="contato-email"' in post_page


def test_hugo_post_page_renders_share_links(built_site):
    destination = built_site
    post_page = (
        destination / "posts" / "2026" / "01" / "05" / "a-cabeca-do-santo" / "index.html"
    ).read_text(encoding="utf-8")
    encoded_url = "https%3A%2F%2Fwww.gustavobelo.com%2Fposts%2F2026%2F01%2F05%2Fa-cabeca-do-santo%2F"

    assert '<aside class="post-share"' in post_page
    assert f'href="https://www.facebook.com/sharer/sharer.php?u={encoded_url}%3Fref%3Dfacebook"' in post_page
    assert f'href="https://www.linkedin.com/sharing/share-offsite/?url={encoded_url}%3Fref%3Dlinkedin"' in post_page
    assert f"{encoded_url}%3Fref%3Dwhatsapp" in post_page
    assert f"url={encoded_url}%3Fref%3Dtelegram" in post_page
    assert 'class="post-share-copy" data-url="https://www.gustavobelo.com/posts/2026/01/05/a-cabeca-do-santo/"' in post_page
    assert 'data-url="https://www.gustavobelo.com/posts/2026/01/05/a-cabeca-do-santo/?ref=share"' in post_page
    assert post_page.count('data-goatcounter-referrer="/posts/2026/01/05/a-cabeca-do-santo/"') == 6


def test_hugo_post_page_falls_back_to_site_image_for_link_previews(built_site):
    destination = built_site
    post_page = (
        destination / "posts" / "2026" / "09" / "25" / "nova-lataria-novas-ideias" / "index.html"
    ).read_text(encoding="utf-8")

    assert '<meta property="og:image" content="https://www.gustavobelo.com/android-chrome-512x512.png">' in post_page


def test_hugo_shelf_renders_works_linking_concluded_posts(built_site_session):
    shelf_page = (built_site_session / "estante" / "index.html").read_text(encoding="utf-8")

    assert '<li class="shelf-item" data-kind="series" data-status="concluded">' in shelf_page
    assert '<a class="shelf-card" href="/posts/2026/10/02/o-segredo-de-widows-bay/"' in shelf_page
    assert 'src="/estante/2026/09/o-segredo-de-widows-bay/cover_' in shelf_page
    assert '.webp"' in shelf_page
    assert '<span class="shelf-status shelf-status-concluded">Concluído</span>' in shelf_page
    assert '<span class="shelf-kind">Série</span>' in shelf_page


def test_hugo_shelf_reuses_post_image_as_cover(built_site_session):
    shelf_page = (built_site_session / "estante" / "index.html").read_text(encoding="utf-8")

    # `cover` points at the post's image, so the processed cover is published
    # next to it instead of copying the original into the shelf bundle.
    assert '<a class="shelf-card" href="/posts/2025/01/05/magicka-2/"' in shelf_page
    assert 'src="/posts/2025/01/05/magicka-2/magicka_hu_' in shelf_page
    assert not (built_site_session / "estante" / "magicka-2").exists()


def test_hugo_shelf_notes_concluded_works_without_a_post(built_site_session):
    shelf_page = (built_site_session / "estante" / "index.html").read_text(encoding="utf-8")
    note = '<span class="shelf-note">Não escrevi nada sobre. Deveria? 🤔</span>'

    # Abbott Elementary is concluded without a post; Widow's Bay links to one.
    abbott = shelf_page.index('alt="Abbott Elementary - 5a temporada"')
    card_start = shelf_page.rindex('<li class="shelf-item"', 0, abbott)
    card_end = shelf_page.index("</li>", abbott)
    card = shelf_page[card_start:card_end]
    assert '<div class="shelf-card shelf-card-unreviewed" tabindex="0"' in card
    assert note in card
    # The click is a GoatCounter event that names the work.
    assert 'data-goatcounter-click="shelf-no-post-abbott-elementary-5a-temporada"' in card
    assert 'data-goatcounter-title="Estante sem resenha: Abbott Elementary - 5a temporada"' in card
    assert shelf_page.count(note) == shelf_page.count("shelf-card-unreviewed")


def test_hugo_shelf_lists_in_progress_first_then_finished_by_month(built_site_session):
    shelf_page = (built_site_session / "estante" / "index.html").read_text(encoding="utf-8")

    in_progress = shelf_page.index('<h3 class="group-title">Em andamento</h3>')
    october = shelf_page.index('<h3 class="group-title">Outubro de 2026</h3>')
    # Concluded on 2026-10-01 (endDate), even though it started in September.
    widows_bay = shelf_page.index('alt="O segredo de Widow&#39;s Bay"')
    assert in_progress < october < widows_bay


def test_hugo_shelf_pages_works_by_year(built_site_session):
    shelf_page = (built_site_session / "estante" / "index.html").read_text(encoding="utf-8")
    current_year = datetime.now().year

    def group_year(title):
        heading = shelf_page.index(f'<h3 class="group-title">{title}</h3>')
        section = shelf_page.rindex('<section class="shelf-group"', 0, heading)
        return shelf_page[section:heading].split('data-year="')[1].split('"')[0]

    # In-progress works belong to the current year; the rest to the year of
    # their month group. shelf.js shows one year at a time, newest first.
    assert group_year("Em andamento") == str(current_year)
    assert group_year("Outubro de 2026") == "2026"
    assert group_year("Dezembro de 2025") == "2025"

    # Hidden until shelf.js runs, so without JavaScript every year is listed.
    nav_start = shelf_page.index('<nav class="shelf-years" aria-label="Anos da estante" hidden>')
    nav = shelf_page[nav_start:shelf_page.index("</nav>", nav_start)]
    assert '<a class="shelf-year" href="?year=2026" data-year="2026" hidden>2026</a>' in nav
    assert '<a class="shelf-year" href="?year=2025" data-year="2025" hidden>2025</a>' in nav
    assert nav.index('data-year="2026"') < nav.index('data-year="2025"')


def test_hugo_shelf_works_have_no_page_of_their_own(built_site_session):
    work_dir = built_site_session / "estante" / "2026" / "09" / "o-segredo-de-widows-bay"

    assert not (work_dir / "index.html").exists()
    assert not (work_dir / "cover.png").exists()
    assert not (built_site_session / "estante" / "index.xml").exists()
    assert not (built_site_session / "estante" / "page" / "2").exists()


def test_hugo_shelf_works_stay_out_of_search_and_sitemap(built_site_session):
    search_index = (built_site_session / "index.json").read_text(encoding="utf-8")
    sitemap = (built_site_session / "sitemap.xml").read_text(encoding="utf-8")

    assert "/estante/" not in search_index
    assert "<loc>https://www.gustavobelo.com/estante/</loc>" in sitemap
    assert "/estante/2026/" not in sitemap


def test_hugo_menu_links_to_shelf(built_site_session):
    homepage = (built_site_session / "index.html").read_text(encoding="utf-8")

    assert 'href="/estante/"' in homepage
