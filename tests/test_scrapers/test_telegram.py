from app.scrapers.telegram import (
    detect_platform,
    extract_codes_from_message,
    parse_discount,
    parse_telegram_message,
)


class TestExtractCodes:
    def test_cupom_prefix(self):
        codes = extract_codes_from_message("Cupom: LEVE20 para desconto")
        assert "LEVE20" in codes

    def test_codigo_prefix(self):
        codes = extract_codes_from_message("Código: VEMCARNAVAL")
        assert "VEMCARNAVAL" in codes

    def test_use_o_cupom(self):
        codes = extract_codes_from_message("Use o cupom SUMMER2026 e ganhe 20% off")
        assert "SUMMER2026" in codes

    def test_quoted_code(self):
        codes = extract_codes_from_message('Aplique o código "PROMO50" no checkout')
        assert "PROMO50" in codes

    def test_filters_false_positives(self):
        codes = extract_codes_from_message("Cupom AMAZON no SITE da LOJA")
        assert "AMAZON" not in codes
        assert "SITE" not in codes
        assert "LOJA" not in codes

    def test_no_codes(self):
        codes = extract_codes_from_message("Sem cupom hoje, mas tem promoção boa")
        assert codes == []

    def test_minimum_length(self):
        codes = extract_codes_from_message("Cupom: AB")
        assert codes == []


class TestDetectPlatform:
    def test_amazon(self):
        assert detect_platform("Cupom Amazon com 20% off") == "amazon_br"

    def test_mercado_livre(self):
        assert detect_platform("Desconto no Mercado Livre") == "mercado_livre"

    def test_ml_abbreviation(self):
        assert detect_platform("Cupom ML para eletrônicos") == "mercado_livre"

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

    def test_free_shipping(self):
        dtype, value = parse_discount("Frete grátis para todo Brasil")
        assert dtype == "free_shipping"
        assert value == 0.0


class TestParseMessage:
    def test_full_message(self):
        msg = "Use o cupom SAVE30 na Amazon e ganhe 30% de desconto em eletrônicos!"
        results = parse_telegram_message(msg)
        assert len(results) == 1
        assert results[0]["code"] == "SAVE30"
        assert results[0]["platform"] == "amazon_br"
        assert results[0]["discount_type"] == "percentage"
        assert results[0]["discount_value"] == 30.0

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
