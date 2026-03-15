from app.scrapers.telegram import (
    detect_platform,
    extract_codes_from_message,
    parse_discount,
    parse_telegram_message,
)


class TestExtractCodes:
    def test_backtick_code(self):
        codes = extract_codes_from_message("Usem o cupom: `VAIBRASIL`")
        assert "VAIBRASIL" in codes

    def test_cupom_prefix(self):
        codes = extract_codes_from_message("Cupom: LEVE20 para desconto")
        assert "LEVE20" in codes

    def test_use_o_cupom(self):
        codes = extract_codes_from_message("Use o cupom SUMMER2026 e ganhe 20% off")
        assert "SUMMER2026" in codes

    def test_usem_o_cupom_backtick(self):
        codes = extract_codes_from_message("🎯 Usem o cupom: `AINDATEMOS`")
        assert "AINDATEMOS" in codes

    def test_quoted_code(self):
        codes = extract_codes_from_message('Aplique o código "PROMO50" no checkout')
        assert "PROMO50" in codes

    def test_filters_false_positives(self):
        codes = extract_codes_from_message("Cupom AMAZON no SITE da LOJA")
        assert "AMAZON" not in codes
        assert "SITE" not in codes
        assert "LOJA" not in codes

    def test_filters_shopee(self):
        codes = extract_codes_from_message("Cupom Shopee BR")
        assert "SHOPEE" not in codes

    def test_no_codes(self):
        codes = extract_codes_from_message("Sem cupom hoje, mas tem promoção boa")
        assert codes == []

    def test_minimum_length(self):
        codes = extract_codes_from_message("Cupom: AB")
        assert codes == []


class TestDetectPlatform:
    def test_amazon(self):
        assert detect_platform("Cupom Amazon com 20% off") == "amazon_br"

    def test_achado_amazon(self):
        assert detect_platform("**Achado Amazon 👇🏻**") == "amazon_br"

    def test_amzn_link(self):
        assert detect_platform("🛒 Link: https://amzn.to/abc") == "amazon_br"

    def test_mercado_livre(self):
        assert detect_platform("Desconto no Mercado Livre") == "mercado_livre"

    def test_achado_mercado_livre(self):
        assert detect_platform("**Achado Mercado Livre 👇🏻**") == "mercado_livre"

    def test_no_platform(self):
        assert detect_platform("Promoção genérica sem plataforma") is None


class TestParseDiscount:
    def test_percentage(self):
        dtype, value = parse_discount("20% OFF em eletrônicos")
        assert dtype == "percentage"
        assert value == 20.0

    def test_fixed_amount(self):
        dtype, value = parse_discount("R$50 de desconto")
        assert dtype == "fixed_amount"
        assert value == 50.0

    def test_fixed_with_space(self):
        dtype, value = parse_discount("R$ 350 OFF em compras")
        assert dtype == "fixed_amount"
        assert value == 350.0

    def test_free_shipping(self):
        dtype, value = parse_discount("Frete grátis para todo Brasil")
        assert dtype == "free_shipping"
        assert value == 0.0


class TestParseMessage:
    def test_real_promotop_message(self):
        msg = """**☑️ Novo Cupom Amazon!**

🔥 R$70 OFF em compras acima de R$599

🎯 Usem o cupom: `AINDATEMOS`

🛒 Resgate nesse produto: https://amzn.to/40trLFZ"""
        results = parse_telegram_message(msg)
        assert len(results) == 1
        assert results[0]["code"] == "AINDATEMOS"
        assert results[0]["platform"] == "amazon_br"
        assert results[0]["discount_type"] == "fixed_amount"
        assert results[0]["discount_value"] == 70.0

    def test_real_ml_message(self):
        msg = """**🔥 Novo Cupom Mercado Livre!**

▪️20% OFF em compras acima de R$599 - Limite de R$159

🎯 Usem o cupom: `VAMOSMELI`

🛒 https://mercadolivre.com/sec/2WVtvGe"""
        results = parse_telegram_message(msg)
        assert len(results) == 1
        assert results[0]["code"] == "VAMOSMELI"
        assert results[0]["platform"] == "mercado_livre"
        assert results[0]["discount_type"] == "percentage"
        assert results[0]["discount_value"] == 20.0

    def test_no_platform_returns_empty(self):
        msg = "Cupom: GENERICO123 para 10% de desconto"
        results = parse_telegram_message(msg)
        assert results == []

    def test_no_code_returns_empty(self):
        msg = "Amazon tem promoção boa hoje"
        results = parse_telegram_message(msg)
        assert results == []

    def test_empty_message(self):
        assert parse_telegram_message("") == []
        assert parse_telegram_message(None) == []

    def test_pechinchou_style_message(self):
        msg = """**Novo cupom na Amazon, ATENÇÃO 😱 É R$ 350 OFF**

•⁠  ⚫ Cupom da Amazon R$ 350 OFF em R$ 2.999

🔥 **R$ 350 OFF**
**Achado Amazon 👇🏻**
🛒 https://pechinchou.com.br/oferta/144001
➡ **Use o cupom:** VAIBRASIL"""
        results = parse_telegram_message(msg)
        assert len(results) == 1
        assert results[0]["code"] == "VAIBRASIL"
        assert results[0]["platform"] == "amazon_br"
        assert results[0]["discount_type"] == "fixed_amount"
        assert results[0]["discount_value"] == 350.0
