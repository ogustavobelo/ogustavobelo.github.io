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
    assert 'src="/estante/o-segredo-de-widows-bay/cover_' in shelf_page
    assert '.webp"' in shelf_page
    assert '<span class="shelf-status shelf-status-concluded">Concluído</span>' in shelf_page
    assert '<span class="shelf-kind">Série</span>' in shelf_page


def test_hugo_shelf_works_have_no_page_of_their_own(built_site_session):
    work_dir = built_site_session / "estante" / "o-segredo-de-widows-bay"

    assert not (work_dir / "index.html").exists()
    assert not (work_dir / "cover.png").exists()
    assert not (built_site_session / "estante" / "index.xml").exists()
    assert not (built_site_session / "estante" / "page" / "2").exists()


def test_hugo_shelf_works_stay_out_of_search_and_sitemap(built_site_session):
    search_index = (built_site_session / "index.json").read_text(encoding="utf-8")
    sitemap = (built_site_session / "sitemap.xml").read_text(encoding="utf-8")

    assert "/estante/" not in search_index
    assert "<loc>https://www.gustavobelo.com/estante/</loc>" in sitemap
    assert "/estante/o-segredo-de-widows-bay/" not in sitemap


def test_hugo_menu_links_to_shelf(built_site_session):
    homepage = (built_site_session / "index.html").read_text(encoding="utf-8")

    assert 'href="/estante/"' in homepage
