# © 2025 Terrabit / Deltatech
# Multi-company tests for l10n_ro_invoice_report

from odoo import Command
from odoo.tests.common import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestL10nRoInvoiceReportMultiCompany(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Second company, with its own chart of accounts and journals.
        cls.company_data_2 = cls.setup_other_company()

        cls.company_a = cls.company_data["company"]
        cls.company_b = cls.company_data_2["company"]

        cls.partner = cls.env["res.partner"].create({"name": "Multi-company Partner"})

        PartnerBank = cls.env["res.partner.bank"]
        cls.bank_a = PartnerBank.create(
            {
                "acc_number": "BANK_A",
                "partner_id": cls.partner.id,
                "company_id": cls.company_a.id,
            }
        )
        cls.bank_b = PartnerBank.create(
            {
                "acc_number": "BANK_B",
                "partner_id": cls.partner.id,
                "company_id": cls.company_b.id,
            }
        )

        # payment_bank_id is company_dependent: one value per company.
        cls.partner.with_company(cls.company_a).payment_bank_id = cls.bank_a
        cls.partner.with_company(cls.company_b).payment_bank_id = cls.bank_b

    def _create_invoice(self, company_data):
        company = company_data["company"]
        return (
            self.env["account.move"]
            .with_company(company)
            .create(
                {
                    "move_type": "out_invoice",
                    "partner_id": self.partner.id,
                    "company_id": company.id,
                    "journal_id": company_data["default_journal_sale"].id,
                    "invoice_line_ids": [
                        Command.create(
                            {
                                "name": "Test Line",
                                "quantity": 1.0,
                                "price_unit": 100.0,
                                "account_id": company_data["default_account_revenue"].id,
                                "tax_ids": [Command.clear()],
                            }
                        )
                    ],
                }
            )
        )

    def test_company_dependent_payment_bank_id(self):
        self.assertEqual(self.partner.with_company(self.company_a).payment_bank_id, self.bank_a)
        self.assertEqual(self.partner.with_company(self.company_b).payment_bank_id, self.bank_b)

    def test_invoice_partner_bank_id_multi_company(self):
        invoice_a = self._create_invoice(self.company_data)
        self.assertEqual(invoice_a.partner_bank_id, self.bank_a)

        invoice_b = self._create_invoice(self.company_data_2)
        self.assertEqual(invoice_b.partner_bank_id, self.bank_b)
