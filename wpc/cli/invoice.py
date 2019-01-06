"""
Entry point for the command line interface.
"""

from calendar import monthrange
from datetime import date, datetime

import click
from dateutil import parser
from dateutil.relativedelta import relativedelta
from tabulate import tabulate

from wpc.model.invoice import Invoice
from wpc.model.invoice_with_hours import InvoiceWithHours
from wpc.repository.workrepo import WorkRepo
from wpc.repository.invoicerepo import InvoiceRepo
from wpc.config.configurator import Configurator
from wpc.doc.doc import Doc

work_repo = WorkRepo()
invoice_repo = InvoiceRepo()
configurator = Configurator()
doc = Doc()


class InvoiceCli:
    pass


@click.group()
def invoice():
    """
    Invoice's commands group.
    """
    return


@click.command()
@click.option('--id', 'id_', type=int, help='The id of the invoice.')
@click.option('--date', type=str, help='The date of the invoice.')
def show(id_, date):
    """
    Shows registered clients. If no filter is specified shows all clients.

    :param id_: The id of the invoice.
    :param date: The date of the invoice.
    """

    # TODO: implements filters.
    invoices = []

    # Find results.
    # if id_ is not None:
    #     res = cli_repo.find(id_)
    #     if res is not None:
    #         clients = [res]
    # elif name is not None:
    #     clients = cli_repo.query()\
    #                 .filter(Customer.name.like("%"+name+"%"))\
    #                 .all()
    # else:
    #     clients = cli_repo.query().all()
    #
    # Print results.

    invoices = invoice_repo.getAllWithHours()

    if len(invoices) <= 0:
        click.echo("No invoices found.")
        return

    headers = ['Date', 'From', 'To', 'Gross', 'Tot. Hours', 'P. Hours', 'Non P. Hours']
    rows = [
        [
            x.emitted_at.strftime("%d/%m/%Y %H:%M"),
            x.from_dt.strftime("%d/%m/%Y"),
            x.to_dt.strftime("%d/%m/%Y"),
            x.gross,
            x.hours_prod + x.hours_non_prod,
            x.hours_prod,
            x.hours_non_prod
        ]
        for x in invoices]

    click.echo(tabulate(rows, headers))

    return


@click.command()
def add():
    """
    Insert an invoice into the system.
    """

    # calculate begin and end of a month ago.
    a_month_ago = date.today()
    a_month_ago = date(a_month_ago.year, a_month_ago.month, 1)
    a_month_ago = a_month_ago + relativedelta(months=-1)

    begin_default = datetime(a_month_ago.year, a_month_ago.month, 1)
    end_default = datetime(a_month_ago.year, a_month_ago.month, monthrange(a_month_ago.year, a_month_ago.month)[1])

    # read values.
    parserinfo = parser.parserinfo(dayfirst=True)
    begin = parser.parse(click.prompt("From", default=begin_default.strftime("%d/%m/%Y")), parserinfo)  # value_proc=parse)#type=click.DateTime(formats=formats), default=begin_default.strftime('%d/%m/%Y'))
    end = parser.parse(click.prompt("To", default=end_default.strftime('%d/%m/%Y')), parserinfo)

    begin = begin.date()
    end = end.date()

    if begin > end:
        raise ValueError("From date cannot be greater than end date")

    click.echo()
    click.echo("Summary:")
    click.echo()

    gross = work_repo.getProfitGrossBetween(begin, end)
    tax = work_repo.getProfitTaxBetween(begin, end)
    net = work_repo.getProfitNetBetween(begin, end)
    hours_tot = work_repo.getHoursBetween(begin, end)
    hours_p = work_repo.getHoursProdBetween(begin, end)
    hours_np = work_repo.getHoursNonProdBetween(begin, end)

    click.echo(tabulate(
        [[
            begin.strftime("%d/%m/%Y"),
            end.strftime("%d/%m/%Y"),
            str(hours_tot),
            str(hours_p),
            str(hours_np),
            str(gross),
            str(tax),
            str(net)]],
        ['Form', 'To', 'Tot. Hours', 'P. Hours', 'Non P. Hours', 'Gross', 'Tax', 'Net']))

    click.echo()

    if not click.confirm("Emit invoice?"):
        click.echo("Invoice not emitted.")
        return

    inv = Invoice.create(begin, end, gross, configurator.customer)
    invoice_repo.create(inv)

    doc.gross = gross
    doc.tax = tax
    doc.net = net
    doc.gross_words = "aaaa"
    doc.date = datetime.today()
    doc.invoice_reason = 'aaaaa'
    doc.progressive = 1

    ret = doc.generate()
    click.echo()

    if ret is False:
        click.echo("Error occurred. To debug the application set the debug flag with config command.")
    else:
        click.echo("Invoice emitted. Locate it at %s" % ret)

    return


@click.command()
@click.argument('id_', type=int, required=True)
def remove(id_):
    """
    Removes an invoices, i.e., marks it as "obsolete". This does not remove the client effectively
    from the system because the data related to it.

    :param id_: The id of the client.
    """

    raise NotImplementedError

    # c = cli_repo.find(id_)
    # if c is None:
    #     click.echo("Client with id %s not found." % id_)
    #     return
    #
    # if click.confirm("Are you sure?"):
    #     cli_repo.remove(c)
    #     click.echo("Success.")
    # else:
    #     click.echo("OK.")

    return


@click.command()
@click.argument('id_', type=int, required=True)
def edit(id_):
    """
    Edit a client.
    :param id_: The id of the client.
    """

    raise NotImplementedError

    # c = cli_repo.find(id_)
    # if c is None:
    #     click.echo("Client with id %s not found." % id_)
    #     return
    #
    # name = click.prompt("Name?", default=c.name, type=str)
    #
    # c.name = name
    # cli_repo.update(c)
    #
    # click.echo("Success.")

    return


invoice.add_command(show)
invoice.add_command(add)
invoice.add_command(remove)
invoice.add_command(edit)