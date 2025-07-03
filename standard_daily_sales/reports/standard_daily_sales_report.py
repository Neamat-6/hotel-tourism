import toolz as T
import toolz.curried as TC
from odoo import _, api, fields, models
from dateutil import rrule


class StandardDailySalesXlsxReport(models.AbstractModel):
  _name = 'report.standard_daily_sales.standard_daily_sales_xlsx_report'
  _inherit = 'report.report_xlsx_dynamic.abstract'
  _description = 'Standard Daily Sales XLSX Report'

  def _classify_data(self, lines, today_date):
    classified_data = {
        'today':
            T.pipe(
                lines,
                TC.filter(lambda line: line['day'] == today_date),
                list,
            ),
        'month':
            T.pipe(
                lines,
                TC.filter(lambda line: line['day'].month == today_date.month if line['day'] else 0),
                list,
            ),
        'year':
            T.pipe(
                lines,
                TC.filter(lambda line: line['day'].year == today_date.year if line['day'] else 0),
                list,
            ),
    }
    return classified_data

  def _sum_pluck_line(self, lines):
    data = {
        'cover': sum(T.pluck('cover', lines)),
        'revenue': sum(T.pluck('revenue', lines)),
        'budget': '#',
    }
    return data

  def _prepare_line(self, title, data):
    intervals = ['today', 'month', 'year']
    common_keys = ['cover', 'revenue', 'budget']
    line = [title]
    for interval in intervals:
      for key in common_keys:
        if key in data[interval]:
          line.extend([data[interval][key]])
    return line

  def _add_style(self, workbook, cell_value, colspan=1, rowspan=1, style=None):
    cell_format = workbook.add_format(style or {})
    return {
        'cell_value': cell_value,
        'colspan': colspan,
        'rowspan': rowspan,
        'cell_format': cell_format,
    }

  def _prepare_room_charge_revenue_data(self, docids, form_data):

    room_charge_revenue_query = """
    WITH HOTEL_ROOM_CHARGE AS (
        SELECT NAME FROM HOTEL_ROOM_CHARGE
        UNION
		SELECT 'Room Charge' AS NAME
    )
    SELECT
      BS.NAME AS DESCRIPTION,
      SUM(BF.NUMBER_OF_GUESTS) AS COVER,
      SUM(BFL.AMOUNT) AS REVENUE,
      '#' AS BUDGET,
      BFL.DAY,
      COALESCE(HB.DAY_USE,FALSE) AS DAY_USE,
      COALESCE(HB.HOUSE_USE,FALSE) AS HOUSE_USE,
      COALESCE(HB.COMPLIMENTARY_ROOM,FALSE) AS COMPLIMENTARY
    FROM HOTEL_BOOKING AS HB
    INNER JOIN BOOKING_FOLIO AS BF ON BF.BOOKING_ID = HB.ID AND HB.COMPANY_ID = %(company_id)s
    INNER JOIN BOOKING_FOLIO_LINE AS BFL ON BFL.FOLIO_ID = BF.ID
        AND HB.STATE != 'cancelled'
        AND BFL.PARTICULARS IN  (SELECT NAME FROM HOTEL_ROOM_CHARGE)
        AND BFL.DAY BETWEEN SYMMETRIC %(today_date)s AND DATE_TRUNC('year', TO_DATE(%(today_date)s, 'YYYY-MM-DD'))::date
    RIGHT JOIN BOOKING_SOURCE AS BS ON BS.NAME = HB.BOOKING_SOURCE
    GROUP BY  (BS.NAME, BFL.DAY,HB.DAY_USE,HB.HOUSE_USE,HB.COMPLIMENTARY_ROOM)
    ORDER BY BS.NAME
    """
    self.env.cr.execute(
        room_charge_revenue_query,
        {
            'today_date': form_data['today_date'],
            'company_id': self.env.company.id,
        },
    )
    room_charge_revenue_data = self.env.cr.dictfetchall()
    today_date = fields.Date.from_string(form_data['today_date'])
    grouped_data = T.pipe(
        room_charge_revenue_data,
        TC.filter(lambda line: not line['day_use']),
        TC.groupby('description'),
        TC.valmap(
            TC.compose_left(
                lambda lines: self._classify_data(lines, today_date),
                TC.valmap(lambda lines: self._sum_pluck_line(lines)),
            )),
    )
    # ['description', 'today_cover', 'today_revenue', 'today_budget', 'month_cover', 'month_revenue', 'month_budget', 'year_cover', 'year_revenue', 'year_budget']
    structured_data = [
        ("title", [["Room Revenue"]]),
        ("lines", [[self._prepare_line(description, date_range_data)]
                   for description, date_range_data in grouped_data.items()]),
    ]
    # =========================================================
    day_use_data = T.pipe(
        room_charge_revenue_data,
        TC.filter(lambda line: line['day_use']),
        list,
        lambda lines: self._classify_data(lines, today_date),
        TC.valmap(lambda lines: self._sum_pluck_line(lines)),
    )
    day_use_line = self._prepare_line('Day Use', day_use_data)
    structured_data.append(("line", [day_use_line]))
    # ===========================================
    house_use_data = T.pipe(
        room_charge_revenue_data,
        TC.filter(lambda line: line['house_use']),
        list,
        lambda lines: self._classify_data(lines, today_date),
        TC.valmap(lambda lines: {
            'cover': len(lines),
            'revenue': 0,
            'budget': 0,
        },),
    )
    house_use_line = self._prepare_line('House Use', house_use_data)
    structured_data.append(("line", [house_use_line]))
    # ===========================================
    complimentary_data = T.pipe(
        room_charge_revenue_data,
        TC.filter(lambda line: line['complimentary']),
        list,
        lambda lines: self._classify_data(lines, today_date),
        TC.valmap(lambda lines: {
            'cover': len(lines),
            'revenue': 0,
            'budget': 0,
        },),
    )
    complimentary_line = self._prepare_line('Complimentary', complimentary_data)
    structured_data.append(("line", [complimentary_line]))
    # ===========================================

    total_data = T.pipe(
        room_charge_revenue_data,
        list,
        lambda lines: self._classify_data(lines, today_date),
        TC.valmap(lambda lines: self._sum_pluck_line(lines)),
    )
    total_line = self._prepare_line('Total', total_data)
    structured_data.append(("total", [total_line]))
    return structured_data

  def _prepare_service_revenue_data(self, docids, form_data):
    service_revenue_query = """
      SELECT
        HS.NAME,
        SUM(BF.NUMBER_OF_GUESTS) AS COVER,
        SUM(BFL.AMOUNT) AS REVENUE,
        '#' AS BUDGET,
        BFL.DAY,
        HS.TYPE
      FROM HOTEL_BOOKING AS HB
      INNER JOIN BOOKING_FOLIO AS BF ON BF.BOOKING_ID = HB.ID AND HB.COMPANY_ID = %(company_id)s
      LEFT JOIN BOOKING_FOLIO_LINE AS BFL ON BFL.FOLIO_ID = BF.ID
      INNER JOIN HOTEL_SERVICES AS HS ON BFL.PARTICULARS = HS.NAME
          AND BFL.DAY BETWEEN SYMMETRIC %(today_date)s AND DATE_TRUNC('year', TO_DATE(%(today_date)s, 'YYYY-MM-DD'))::date
      GROUP BY  ( BFL.DAY,HS.NAME,HS.TYPE )
    """
    self.env.cr.execute(
        service_revenue_query,
        {
            'today_date': form_data['today_date'],
            'company_id': self.env.company.id,
        },
    )
    service_revenue_data = self.env.cr.dictfetchall()
    today_date = fields.Date.from_string(form_data['today_date'])
    grouped_data = T.pipe(
        service_revenue_data,
        TC.groupby('type'),
        TC.valmap(
            TC.compose_left(
                TC.groupby('name'),
                TC.valmap(
                    TC.compose_left(
                        lambda lines: self._classify_data(lines, today_date),
                        TC.valmap(lambda lines: self._sum_pluck_line(lines)),
                    )),
            )),
    )
    # =========================================================
    total_data = T.pipe(
        service_revenue_data,
        TC.groupby('type'),
        TC.valmap(
            TC.compose_left(
                lambda lines: self._classify_data(lines, today_date),
                TC.valmap(lambda lines: self._sum_pluck_line(lines)),
            )),
    )
    structured_data = [("title", [["Services"]])]
    for service_type, service_data in grouped_data.items():
      structured_data.append(("subtitle", [[service_type]]))
      for service_name, data in service_data.items():
        structured_data.append(("line", [self._prepare_line(service_name, data)]))
    # =========================================================
      total_line = self._prepare_line(f"{service_type} Total", total_data[service_type])
      structured_data.append(("total", [total_line]))
    return structured_data

  def _prepare_pos_revenue_data(self, docids, form_data):
    today_date = fields.Date.from_string(form_data['today_date'])
    pos_revenue_query = """
      SELECT
        POSC.NAME AS POS_NAME,
        PC.NAME AS CATEG_NAME,
        SUM(POSOL.QTY) AS COVER,
        SUM(POSOL.PRICE_SUBTOTAL) AS REVENUE,
        '#' AS BUDGET,
        POSO.DATE_ORDER::DATE AS DAY
      FROM POS_ORDER_LINE AS POSOL
        INNER JOIN POS_ORDER AS POSO ON POSO.ID = POSOL.ORDER_ID
          AND POSO.COMPANY_ID = %(company_id)s
          AND POSO.DATE_ORDER::DATE BETWEEN SYMMETRIC  %(today_date)s
          AND DATE_TRUNC('year', TO_DATE( %(today_date)s, 'YYYY-MM-DD'))::DATE
        LEFT JOIN POS_SESSION AS POSS ON POSS.ID = POSO.SESSION_ID
        LEFT JOIN POS_CONFIG AS POSC ON POSC.ID = POSS.CONFIG_ID
        LEFT JOIN PRODUCT_PRODUCT AS PP ON PP.ID = POSOL.PRODUCT_ID
        LEFT JOIN PRODUCT_TEMPLATE AS PT ON PT.ID = PP.PRODUCT_TMPL_ID
        LEFT JOIN PRODUCT_CATEGORY AS PC ON PC.ID = PT.categ_id
      GROUP BY POSC.NAME,PC.NAME,POSO.DATE_ORDER
    """
    self.env.cr.execute(pos_revenue_query, {
        "today_date": form_data['today_date'],
        "company_id": self.env.company.id,
    })
    pos_revenue_data = self.env.cr.dictfetchall()
    grouped_data = T.pipe(
        pos_revenue_data,
        TC.groupby('pos_name'),
        TC.valmap(
            TC.compose_left(
                TC.groupby('categ_name'),
                TC.valmap(
                    TC.compose_left(
                        lambda lines: self._classify_data(lines, today_date),
                        TC.valmap(lambda lines: self._sum_pluck_line(lines)),
                    )),
            )),
    )
    total_data = T.pipe(
        pos_revenue_data,
        TC.groupby('pos_name'),
        TC.valmap(
            TC.compose_left(
                lambda lines: self._classify_data(lines, today_date),
                TC.valmap(lambda lines: self._sum_pluck_line(lines)),
            )),
    )

    structured_data = [("title", [["POS"]])]
    for pos_name, pos_data in grouped_data.items():
      structured_data.append(("subtitle", [[f"{pos_name} Revenue"]]))
      for categ_name, data in pos_data.items():
        structured_data.append(("line", [self._prepare_line(categ_name, data)]))
      total_line = self._prepare_line(f"{pos_name} Total", total_data[pos_name])
      structured_data.append(("total", [total_line]))
    return structured_data

  def _prepare_payment_data(self, docids, form_data):
    payment_query = """
    SELECT AJ.NAME,
      SUM(AP.AMOUNT) AS REVENUE,
      AP.AUDIT_DATE  AS DAY
      FROM ACCOUNT_PAYMENT AS AP
      INNER JOIN HOTEL_BOOKING AS HB ON HB.ID = AP.BOOKING_ID
        AND AP.AUDIT_DATE BETWEEN SYMMETRIC  %(today_date)s AND DATE_TRUNC('year', TO_DATE( %(today_date)s, 'YYYY-MM-DD'))::DATE
        AND HB.COMPANY_ID = %(company_id)s
      LEFT JOIN ACCOUNT_MOVE AS AM ON AM.ID = AP.MOVE_ID
      LEFT JOIN ACCOUNT_JOURNAL AS AJ ON AJ.ID = AM.JOURNAL_ID
    GROUP BY AJ.NAME,AP.AUDIT_DATE
    """
    self.env.cr.execute(payment_query, {
        "today_date": form_data['today_date'],
        "company_id": self.env.company.id,
    })
    payment_data = self.env.cr.dictfetchall()
    today_date = fields.Date.from_string(form_data['today_date'])
    grouped_data = T.pipe(
        payment_data,
        TC.groupby('name'),
        TC.valmap(
            TC.compose_left(
                lambda lines: self._classify_data(lines, today_date),
                TC.valmap(lambda lines: {"revenue": sum(T.pluck('revenue', lines))}),
            )),
    )
    structured_data = [
        ("title", [["Payments"]]),
        ("total", [[None, "Today", "M.T.D", "Y.T.D"]]),
    ]

    for payment_name, data in grouped_data.items():
      structured_data.append(("total", [self._prepare_line(payment_name, data)]))
    return structured_data

    # =========================================================

  def _prepare_statistics_figures_data(self, docids, form_data, room_charge_revenue_data):

    def divide(numerator, denominator):
      if denominator == 0:
        return 0
      else:
        return numerator / denominator

    company_id = self.env.company.id,
    # today_date = fields.Date.today()
    today_date = fields.Date.from_string(form_data['today_date'])
    mtd_days = len(
        list(rrule.rrule(
            rrule.DAILY,
            dtstart=today_date.replace(day=1),
            until=today_date,
        )))
    ytd_days = len(
        list(rrule.rrule(
            rrule.DAILY,
            dtstart=today_date.replace(month=1, day=1),
            until=today_date,
        )))
    hotel_room_ids_counter = self.env['hotel.room'].search_count([('company_id', '=', company_id)])
    out_of_order_rooms_query = """
    SELECT DATETIME::DATE AS DAY,NOTES,ROOM_ID
    FROM AUDIT_TRAILS
    WHERE OPERATION = 'update_room_stay_state'
	AND NOTES ilike '%%To Stay Status: Out of Order%%'
	AND DATETIME::DATE BETWEEN SYMMETRIC %(today_date)s AND DATE_TRUNC('year', TO_DATE(%(today_date)s, 'YYYY-MM-DD'))::DATE
    """
    self.env.cr.execute(out_of_order_rooms_query,{
        'today_date': form_data['today_date'],
        'company_id': self.env.company.id,
    })
    out_of_order_rooms_data = self.env.cr.dictfetchall()
    out_of_order_rooms = T.pipe(
        out_of_order_rooms_data,
        lambda lines: self._classify_data(lines, today_date),
        TC.valmap(TC.count),

    )

    complimentary_and_house_use_rooms = """
        WITH HOTEL_ROOM_CHARGE AS (
        SELECT NAME FROM HOTEL_ROOM_CHARGE
        UNION
		SELECT 'Room Charge' AS NAME
    )
    SELECT
      BFL.DAY,
      COUNT(*) AS TOTAL,
      CASE WHEN HB.HOUSE_USE = TRUE THEN 'house_use' ELSE 'complimentary' END AS TYPE
    FROM HOTEL_BOOKING AS HB
    INNER JOIN BOOKING_FOLIO AS BF ON BF.BOOKING_ID = HB.ID AND HB.COMPANY_ID = %(company_id)s
    INNER JOIN BOOKING_FOLIO_LINE AS BFL ON BFL.FOLIO_ID = BF.ID
        AND HB.STATE != 'cancelled'
		AND  (HB.HOUSE_USE = TRUE OR HB.COMPLIMENTARY_ROOM)
        AND BFL.PARTICULARS IN  (SELECT NAME FROM HOTEL_ROOM_CHARGE)
        AND BFL.DAY BETWEEN SYMMETRIC %(today_date)s AND DATE_TRUNC('year', TO_DATE(%(today_date)s, 'YYYY-MM-DD'))::date
    GROUP BY  (BFL.DAY,HB.HOUSE_USE,HB.COMPLIMENTARY_ROOM)
    """
    self.env.cr.execute(complimentary_and_house_use_rooms, {
        'today_date': form_data['today_date'],
        'company_id': self.env.company.id,
    })
    complimentary_and_house_use_rooms_data = self.env.cr.dictfetchall()
    structured_complimentary_and_house_use = T.pipe(
        complimentary_and_house_use_rooms_data, TC.groupby('type'),
        TC.valmap(
            TC.compose_left(
                lambda lines: self._classify_data(lines, today_date),
                TC.valmap(TC.pluck('total')),
                TC.valmap(sum),
            )))
    number_of_guests = {
        'today': room_charge_revenue_data[-1][1][0][1],
        'month': room_charge_revenue_data[-1][1][0][4],
        'year': room_charge_revenue_data[-1][1][0][7],
    }

    total_day_use_booked_rooms_query = """
    SELECT BFL.DAY AS DAY,	COUNT(BFL.*) AS BOOKED
    FROM BOOKING_FOLIO_LINE AS BFL
        INNER JOIN BOOKING_FOLIO AS BF ON BF.ID = BFL.FOLIO_ID
        AND BF.STATE != 'cancelled'
        AND BF.COMPANY_ID IS NOT NULL
        AND BF.ROOM_TYPE_ID IS NOT NULL
        AND BF.COMPANY_ID =  %(company_id)s
        AND BFL.PARTICULARS = 'Room Charge'
        AND BF.DAY_USE = TRUE
        AND BFL.DAY BETWEEN SYMMETRIC %(today_date)s AND DATE_TRUNC('year', TO_DATE(%(today_date)s, 'YYYY-MM-DD'))::date
    GROUP BY BFL.DAY
    """
    self.env.cr.execute(total_day_use_booked_rooms_query, {
        'today_date': form_data['today_date'],
        'company_id': self.env.company.id,
    })
    total_day_use_booked_rooms_data = self.env.cr.dictfetchall()
    total_day_use_booked_rooms = T.pipe(
        total_day_use_booked_rooms_data,
        lambda lines: self._classify_data(lines, today_date),
        TC.valmap(TC.map(TC.get('booked'))),
        TC.valmap(sum),
    )
    total_booked_rooms_query = """
    SELECT BFL.DAY AS DAY,	COUNT(BFL.*) AS BOOKED
    FROM BOOKING_FOLIO_LINE AS BFL
        INNER JOIN BOOKING_FOLIO AS BF ON BF.ID = BFL.FOLIO_ID
        AND BF.STATE != 'cancelled'
        AND BF.COMPANY_ID IS NOT NULL
        AND BF.ROOM_TYPE_ID IS NOT NULL
        AND BF.COMPANY_ID =  %(company_id)s
        AND BFL.PARTICULARS = 'Room Charge'
        AND BFL.DAY BETWEEN SYMMETRIC %(today_date)s AND DATE_TRUNC('year', TO_DATE(%(today_date)s, 'YYYY-MM-DD'))::date
    GROUP BY BFL.DAY
    """
    self.env.cr.execute(total_booked_rooms_query, {
        'today_date': form_data['today_date'],
        'company_id': self.env.company.id,
    })
    total_booked_rooms_data = self.env.cr.dictfetchall()
    total_booked_rooms = T.pipe(
        total_booked_rooms_data,
        lambda lines: self._classify_data(lines, today_date),
        TC.valmap(TC.map(TC.get('booked'))),
        TC.valmap(sum),
    )
    total_booked_rooms_without_comp_and_hu = {
        'today':
            total_booked_rooms.get('today', 0) -
            structured_complimentary_and_house_use.get('complimentary', {}).get('today', 0) -
            structured_complimentary_and_house_use.get('house_use', {}).get('today', 0),
        'month':
            total_booked_rooms.get('month', 0) -
            structured_complimentary_and_house_use.get('complimentary', {}).get('month', 0) -
            structured_complimentary_and_house_use.get('house_use', {}).get('month', 0),
        'year':
            total_booked_rooms.get('year', 0) -
            structured_complimentary_and_house_use.get('complimentary', {}).get('year', 0) -
            structured_complimentary_and_house_use.get('house_use', {}).get('year', 0),
    }

    # ======================================    AVERAGE RATE WITH AND WITHOUT COMPLIMENTARY AND HOUSE USE ========================================
    average_rate_without_comp_and_hu = {
        'today':
            0 if not total_booked_rooms.get('today', 1) else room_charge_revenue_data[-1][1][0][2] /
            total_booked_rooms_without_comp_and_hu.get('today', 1),
        'month':
            0 if not total_booked_rooms.get('month', 1) else room_charge_revenue_data[-1][1][0][5] /
            total_booked_rooms_without_comp_and_hu.get('month', 1),
        'year':
            0 if not total_booked_rooms.get('year', 1) else room_charge_revenue_data[-1][1][0][8] /
            total_booked_rooms_without_comp_and_hu.get('year', 1),
    }
    average_rate_with_comp_and_hu = {
        'today':
            0 if not total_booked_rooms.get('today', 1) else room_charge_revenue_data[-1][1][0][2] /
            total_booked_rooms.get('today', 1),
        'month':
            0 if not total_booked_rooms.get('month', 1) else room_charge_revenue_data[-1][1][0][5] /
            total_booked_rooms.get('month', 1),
        'year':
            0 if not total_booked_rooms.get('year', 1) else room_charge_revenue_data[-1][1][0][8] /
            total_booked_rooms.get('year', 1),
    }
    # ======================================    OCCUPANCY WITH AND WITHOUT COMPLIMENTARY AND HOUSE USE ========================================
    occupancy_with_comp_and_hu = {
        'month': divide(total_booked_rooms.get('month', 0), hotel_room_ids_counter),
        'today': divide(total_booked_rooms.get('today', 0), hotel_room_ids_counter),
        'year': divide(total_booked_rooms.get('year', 0), hotel_room_ids_counter)
    }

    occupancy_without_comp_and_hu = {
        'today':
            divide(
                total_booked_rooms.get('today', 0),
                (hotel_room_ids_counter -
                 structured_complimentary_and_house_use.get('complimentary', {}).get('today', 0) -
                 structured_complimentary_and_house_use.get('house_use', {}).get('today', 0)),
            ),
        'month':
            divide(
                total_booked_rooms.get('month', 0),
                (hotel_room_ids_counter -
                 structured_complimentary_and_house_use.get('complimentary', {}).get('month', 0) -
                 structured_complimentary_and_house_use.get('house_use', {}).get('month', 0)),
            ),
        'year':
            divide(
                total_booked_rooms.get('year', 0),
                (hotel_room_ids_counter -
                 structured_complimentary_and_house_use.get('complimentary', {}).get('year', 0) -
                 structured_complimentary_and_house_use.get('house_use', {}).get('year', 0)),
            ),
    }

    # ======================================    REV PAR ========================================
    rev_par = {
        'today':
            0 if not total_booked_rooms.get('today', 1) else room_charge_revenue_data[-1][1][0][2] /
            hotel_room_ids_counter,
        'month':
            0 if not total_booked_rooms.get('month', 1) else room_charge_revenue_data[-1][1][0][5] /
            (hotel_room_ids_counter * mtd_days),
        'year':
            0 if not total_booked_rooms.get('year', 1) else room_charge_revenue_data[-1][1][0][8] /
            (hotel_room_ids_counter * ytd_days),
    }
    # =====================================    Double Occupancy ========================================
    double_occupancy_query = """
    SELECT  ROOM_ID,DAY,COUNT(*) AS DOUBLE_OCCUPANCY
    FROM BOOKING_FOLIO_LINE
        WHERE DAY BETWEEN SYMMETRIC %(today_date)s AND DATE_TRUNC('year', TO_DATE(%(today_date)s, 'YYYY-MM-DD'))::date
        AND PARTICULARS = 'Room Charge'
        AND ROOM_ID IS NOT NULL
        AND FOLIO_STATE != 'cancelled'
        AND COMPANY_ID = %(company_id)s
        AND TYPE = 'room_charge'
    GROUP BY ROOM_ID,DAY
    HAVING COUNT(*) > 1
    ORDER BY DAY
    """
    self.env.cr.execute(double_occupancy_query, {
        'today_date': form_data['today_date'],
        'company_id': self.env.company.id,
    })
    double_occupancy_data = self.env.cr.dictfetchall()
    double_occupancy = T.pipe(
        double_occupancy_data,
        lambda lines: self._classify_data(lines, today_date),
        TC.valmap(TC.count),
    )

    # =========================================================================================

    statistics_figures_data = {
        'total_rooms': [
            "Total Rooms In Hotel",
            None,
            hotel_room_ids_counter,
            None,
            None,
            hotel_room_ids_counter * mtd_days,
            None,
            None,
            hotel_room_ids_counter * ytd_days,
            None,
        ],
        'vacant_rooms': [
            "Vaccant  Rooms",
            None,
            hotel_room_ids_counter - total_booked_rooms.get('today', 0) + total_day_use_booked_rooms.get('today', 0),
            None,
            None,
            hotel_room_ids_counter * mtd_days - total_booked_rooms.get('month', 0) + total_day_use_booked_rooms.get('month', 0),
            None,
            None,
            hotel_room_ids_counter * ytd_days - total_booked_rooms.get('year', 0) + total_day_use_booked_rooms.get('year', 0),
            None,
        ],
        'out_of_order_rooms': [
            "Out Of Orer Rooms",
            None,
            out_of_order_rooms.get('today', 0),
            None,
            None,
            out_of_order_rooms.get('month', 0),
            None,
            None,
            out_of_order_rooms.get('year', 0),
            None,
        ],
        'occupied_rooms': [
            "Occupied Rooms-Comp",
            None,
            divide(structured_complimentary_and_house_use.get('complimentary', {}).get('today', 0) , total_booked_rooms.get('today', 1)),
            None,
            None,
            divide(structured_complimentary_and_house_use.get('complimentary', {}).get('month', 0) , total_booked_rooms.get('month', 1)),
            None,
            None,
            divide(structured_complimentary_and_house_use.get('complimentary', {}).get('year', 0) , total_booked_rooms.get('year', 1)),
            None,
        ],
        'complimentary_rooms': [
            "Complimentary Rooms",
            None,
            structured_complimentary_and_house_use.get('complimentary', {}).get('today', 0),
            None,
            None,
            structured_complimentary_and_house_use.get('complimentary', {}).get('month', 0),
            None,
            None,
            structured_complimentary_and_house_use.get('complimentary', {}).get('year', 0),
            None,
        ],
        'house_use_rooms': [
            "House Use Rooms",
            None,
            structured_complimentary_and_house_use.get('house_use', {}).get('today', 0),
            None,
            None,
            structured_complimentary_and_house_use.get('house_use', {}).get('month', 0),
            None,
            None,
            structured_complimentary_and_house_use.get('house_use', {}).get('year', 0),
            None,
        ],
        'no_of_guests': [
            "No. of Guests",
            None,
            number_of_guests.get('today', 0),
            None,
            None,
            number_of_guests.get('month', 0),
            None,
            None,
            number_of_guests.get('year', 0),
            None,
        ],
        'occupancy_with_comp_and_hu': [
            "Occupancy (With Comp.& H.U)",
            None,
            hotel_room_ids_counter -
            structured_complimentary_and_house_use.get('complimentary', {}).get('today', 0),
            None,
            None,
            hotel_room_ids_counter * mtd_days -
            structured_complimentary_and_house_use.get('complimentary', {}).get('month', 0),
            None,
            None,
            hotel_room_ids_counter * ytd_days -
            structured_complimentary_and_house_use.get('complimentary', {}).get('year', 0),
            None,
        ],
        "average_rate_without_comp_and_hu": [
            "Average Rate (Without Comp &H.U)",
            None,
            average_rate_without_comp_and_hu.get('today', 0),
            None,
            None,
            average_rate_without_comp_and_hu.get('month', 0),
            None,
            None,
            average_rate_without_comp_and_hu.get('year', 0),
            None,
        ],
        "average_rate_with_comp_and_hu": [
            "Average Rate (With Comp.& H.U)",
            None,
            average_rate_with_comp_and_hu.get('today', 0),
            None,
            None,
            average_rate_with_comp_and_hu.get('month', 0),
            None,
            None,
            average_rate_with_comp_and_hu.get('year', 0),
            None,
        ],
        "occupancy_with_comp_and_hu": [
            "Occupancy (With Comp.& H.U)",
            None,
            occupancy_with_comp_and_hu.get('today', 0),
            None,
            None,
            occupancy_with_comp_and_hu.get('month', 0),
            None,
            None,
            occupancy_with_comp_and_hu.get('year', 0),
            None,
        ],
        "occupancy_without_comp_and_hu": [
            "Occupancy (Without Comp.& H.U)",
            None,
            occupancy_without_comp_and_hu.get('today', 0),
            None,
            None,
            occupancy_without_comp_and_hu.get('month', 0),
            None,
            None,
            occupancy_without_comp_and_hu.get('year', 0),
            None,
        ],
        "rev_par": [
            "Rev Par",
            None,
            rev_par.get('today', 0),
            None,
            None,
            rev_par.get('month', 0),
            None,
            None,
            rev_par.get('year', 0),
            None,
        ],
        "double_occupancy": [
            "Double Occupancy",
            None,
            double_occupancy.get('today', 0),
            None,
            None,
            double_occupancy.get('month', 0),
            None,
            None,
            double_occupancy.get('year', 0),
            None,
        ],
    }
    return statistics_figures_data

  @api.model
  def _prepare_report_data(self, docids, data):
    room_charge_revenue_data = self._prepare_room_charge_revenue_data(docids, data)
    service_revenue_data = self._prepare_service_revenue_data(docids, data)
    pos_revenue_data = self._prepare_pos_revenue_data(docids, data)
    payment_data = self._prepare_payment_data(docids, data)
    statistics_figures_data = self._prepare_statistics_figures_data(
        docids,
        data,
        room_charge_revenue_data,
    )
    result = {
        "room_charge_revenue_data": room_charge_revenue_data,
        "service_revenue_data": service_revenue_data,
        "pos_revenue_data": pos_revenue_data,
        "payment_data": payment_data,
        "statistics_figures_data": statistics_figures_data,
    }
    return result

  def generate_xlsx_report(self, workbook, form_data, docids):

    def prepare_custom_cell(cell_value, colspan=1, rowspan=1, style=None):
      cell_format = workbook.add_format(style or {})
      return {
          'cell_value': cell_value,
          'colspan': colspan,
          'rowspan': rowspan,
          'cell_format': cell_format,
      }

    def add_style(lines):
      result = []
      for key, data in lines:
        if key == 'title':
          styled_data = T.pipe(
              data,
              TC.map(lambda line: map(
                  lambda cell: prepare_custom_cell(
                      cell,
                      style={
                          'bold': True,
                          'border': True,
                          'bg_color': 'yellow',
                      },
                      colspan=10,
                  ),
                  line,
              )),
          )
        elif key == 'subtitle':
          styled_data = T.pipe(
              data,
              TC.map(lambda line: map(
                  lambda cell: prepare_custom_cell(
                      cell,
                      style={
                          'bold': True,
                          'border': True,
                          'bg_color': '#ffefd5',
                      },
                      colspan=10,
                  ),
                  line,
              )),
          )
        elif key == 'line':
          styled_data = T.pipe(
              data,
              TC.map(lambda line: map(
                  lambda cell: prepare_custom_cell(
                      cell,
                      style={
                          'border': True,
                      },
                  ),
                  line,
              )),
          )
        elif key == 'lines':
          styled_data = T.pipe(
              data,
              TC.map(lambda line: map(
                  lambda cell: prepare_custom_cell(
                      cell,
                      style={
                          'border': True,
                      },
                  ),
                  line[0],
              )),
          )
        elif key == 'total':
          styled_data = T.pipe(
              data,
              TC.map(lambda line: map(
                  lambda cell: prepare_custom_cell(
                      cell,
                      style={
                          'bold': True,
                          'border': True,
                          'bg_color': '#ccffcc',
                      },
                  ),
                  line,
              )),
          )
        # else:
        #   styled_data = data

        result.extend(styled_data)
      return result


    report_name = _('Standard Daily Sales Report')
    report_header = [
        [
            form_data['today_date'],
            prepare_custom_cell(
                self.env.company.name,
                style={
                    'bold': True,
                    'align': 'center'
                },
                colspan=9,
            ),
        ],
        [prepare_custom_cell('', colspan=10)],
        [
            prepare_custom_cell(
                "Description",
                style={
                    'bold': True,
                    'border': True,
                    'valign': 'vcenter'
                },
                rowspan=2,
            ),
            prepare_custom_cell(
                "Today",
                style={
                    'bold': True,
                    'border': True,
                    'align': 'center',
                },
                colspan=3,
            ),
            prepare_custom_cell(
                "Month to Date",
                style={
                    'bold': True,
                    'border': True,
                    'align': 'center',
                },
                colspan=3,
            ),
            prepare_custom_cell(
                "Year to Date",
                style={
                    'bold': True,
                    'border': True,
                    'align': 'center',
                },
                colspan=3,
            ),
        ],
        map(
            lambda cell: prepare_custom_cell(
                cell,
                style={
                    'bold': True,
                    'border': True,
                    'top': 6
                },
            ),
            [None, *["Cover", "Actual", "Budget"] * 3],
        ),
    ]
    report_body = self._prepare_report_data(docids, form_data)
    room_charge_revenue_data = add_style(report_body.get('room_charge_revenue_data'))
    service_revenue_data = add_style(report_body.get('service_revenue_data'))
    pos_revenue_data = add_style(report_body.get('pos_revenue_data'))
    payment_data = add_style(report_body.get('payment_data'))
    statistics_figures_data = report_body.get('statistics_figures_data', {})

    report_body = T.pipe(
        self._prepare_report_data(docids, form_data),
        TC.map(lambda line: map(
            lambda cell: prepare_custom_cell(
                cell,
                style={
                    'border': True,
                },
            ),
            line,
        )),
    )
    statics_figures = [
        [
            prepare_custom_cell(
                "Statistics Figures",
                style={
                    'bold': True,
                    'align': 'center',
                    'border': True,
                },
                colspan=10,
            )
        ],
        *T.pipe(
            [
                [None, *[None, "ACTUAL", "Budget"] * 3],
                statistics_figures_data.get('total_rooms', []),
                statistics_figures_data.get('vacant_rooms', []),
                statistics_figures_data.get('out_of_order_rooms', []),
                statistics_figures_data.get('occupied_rooms', []),
                statistics_figures_data.get('complimentary_rooms', []),
                statistics_figures_data.get('house_use_rooms', []),
                statistics_figures_data.get('no_of_guests', []),
                statistics_figures_data.get('average_rate_with_comp_and_hu', []),
                statistics_figures_data.get('rev_par', []),
                statistics_figures_data.get('occupancy_with_comp_and_hu', []),
                statistics_figures_data.get('occupancy_without_comp_and_hu', []),
                statistics_figures_data.get('double_occupancy', []),
                statistics_figures_data.get('average_rate_without_comp_and_hu', []),
                [None] * 10,
            ],
            TC.map(lambda line: map(lambda cell: prepare_custom_cell(
                cell,
                style={'border': True},
            ), line)),
        ),
    ]

    footer = [
        [None, None, None, None],
        [None, None, None, None],
        [None, None, None, None],
        [
            prepare_custom_cell(
                "Income Auditor",
                style={
                    'bold': True,
                    'underline': True,
                    'border': True,
                },
            ),
            *[None] * 5,
            prepare_custom_cell(
                "Financial Controller",
                style={
                    'bold': True,
                    'underline': True,
                    'border': True,
                },
            ),
        ],
    ]

    sheet = workbook.add_worksheet(report_name[:31])
    sheet.set_column(0, 0, 30)
    sheet.set_column(1, 9, 10)
    self.write_dynamic_report(
        sheet,
        TC.concatv(
            report_header,
            room_charge_revenue_data,
            service_revenue_data,
            pos_revenue_data,
            statics_figures,
            payment_data,
            footer,
        ))
