from odoo import models, fields, api


class HotelTransportationContract(models.Model):
    _name = "hotel.transportation.contract"
    _description = "Hotel Transportation Contract"

    name = fields.Char(string="Contract Name")
    contract_type = fields.Selection(
        string="Contract Type",
        selection=[("purchase", "Purchase"), ("sell", "Sell")],
        required=True
    )

    partner_id = fields.Many2one(
        'res.partner', 
        string='Customer',
        default=lambda x: x.env.company.hotel_default_customer_id.id
    )

    travel_agent_name = fields.Many2one('res.partner', string='Travel Agent Name')

    person_name = fields.Char(string="Person Name", compute="_compute_person_name")

    hotel_transportation_contract_lines = fields.One2many(
        'hotel.transportation.contract.lines', 
        'hotel_transportation_contract_lines_id', 
        string="Contract Lines"
    )

    has_valid_package_lines = fields.Boolean(
        string="Has Valid Package Lines", 
        compute="_compute_valid_package_lines"
    )

    @api.depends("hotel_transportation_contract_lines")
    def _compute_valid_package_lines(self):
        for record in self:
            valid_lines = record.hotel_transportation_contract_lines.filtered(
                lambda line: line.package_id and line.price > 0
            )
            record.has_valid_package_lines = bool(valid_lines)

    @api.depends("contract_type", "partner_id", "travel_agent_name")
    def _compute_person_name(self):
        for record in self:
            if record.contract_type == "sell":
                record.person_name = record.partner_id.name
            elif record.contract_type == "purchase":
                record.person_name = record.travel_agent_name.name
            else:
                record.person_name = ""

    def name_get(self):
        result = []
        for record in self:
            name = f"Contract ({record.contract_type})"
            if record.contract_type == "sell":
                name += f" with Customer: {record.partner_id.name}"
            elif record.contract_type == "purchase":
                name += f" with Travel Agent: {record.travel_agent_name.name}"
            result.append((record.id, name))
        return result

    
    
    
class HotelTransportationContractLines(models.Model):
    _name="hotel.transportation.contract.lines"
    _description="Hotel Transportation Contract Lines"
    
    
    package_id = fields.Many2one("hotel.transport.package", string="Package", required=True)
    
    price = fields.Float("price", required=True)
    
    
    hotel_transportation_contract_lines_id = fields.Many2one('hotel.transportation.contract', string="Contract", required=True, ondelete="cascade")