{#

DO NOT USE THIS AS A BASE,
IF YOU ARE COPY AND PASTING THIS FILE
YOU ARE PROBABLY DOING THINGS INCORRECTLY.

Null template, does nothing except defining a basic structure
To layout the different blocks of a notebook.

Subtemplates can override blocks to define their custom representation.

If one of the block you do overwrite is not a leave block, consider
calling super.

{%- block nonLeaveBlock -%}
    #add stuff at beginning
    {{ super() }}
    #add stuff at end
{%- endblock nonLeaveBlock -%}

consider calling super even if it is a leave block, we might insert more blocks later.

#}
{%- block header -%}
{%- endblock header -%}
{%- block body -%}
{%- for worksheet in nb.worksheets -%}
    {%- for cell in worksheet.cells -%}
        {%- block any_cell scoped -%}
            {%- if cell.cell_type in ['code'] -%}
                {%- block codecell scoped -%}
                    {%- block input_group -%}
                        {%- block in_prompt -%}{%- endblock in_prompt -%}
                        {%- block input -%}{%- endblock input -%}
                    {%- endblock input_group -%}
                    {%- if cell.outputs -%}
                    {%- block output_group -%}
                        {%- block output_prompt -%}{%- endblock output_prompt -%}
                        {%- block outputs scoped -%}
                            {%- for output in cell.outputs -%}
                                {%- block output scoped -%}
                                    {%- if output.output_type in ['pyout'] -%}
                                        {%- block pyout scoped -%}{%- endblock pyout -%}
                                    {%- elif output.output_type in ['stream'] -%}
                                        {%- block stream scoped -%}
                                            {%- if output.stream in ['stdout'] -%}
                                                {%- block stream_stdout scoped -%}
                                                {%- endblock stream_stdout -%}
                                            {%- elif output.stream in ['stderr'] -%}
                                                {%- block stream_stderr scoped -%}
                                                {%- endblock stream_stderr -%}
                                            {%- endif -%}
                                        {%- endblock stream -%}
                                    {%- elif output.output_type in ['display_data'] -%}
                                        {%- block display_data scoped -%}
                                            {%- block data_priority scoped -%}
                                            {%- endblock data_priority -%}
                                        {%- endblock display_data -%}
                                    {%- elif output.output_type in ['pyerr'] -%}
                                        {%- block pyerr scoped -%}
                                        {%- for line in output.traceback -%}
                                            {%- block traceback_line scoped -%}{%- endblock traceback_line -%}
                                        {%- endfor -%}
                                        {%- endblock pyerr -%}
                                    {%- endif -%}
                                {%- endblock output -%}
                            {%- endfor -%}
                        {%- endblock outputs -%}
                    {%- endblock output_group -%}
                    {%- endif -%}
                {%- endblock codecell -%}
            {%- elif cell.cell_type in ['markdown'] -%}
                {%- block markdowncell scoped-%}
                {%- endblock markdowncell -%}
            {%- elif cell.cell_type in ['heading'] -%}
                {%- block headingcell scoped-%}
                {%- endblock headingcell -%}
            {%- elif cell.cell_type in ['raw'] -%}
                {%- block rawcell scoped -%}
                {% if cell.metadata.get('raw_mimetype', '').lower() in resources.get('raw_mimetypes', ['']) %}
                {{ cell.source }}
                {% endif %}
                {%- endblock rawcell -%}
            {%- else -%}
                {%- block unknowncell scoped-%}
                {%- endblock unknowncell -%}
            {%- endif -%}
        {%- endblock any_cell -%}
    {%- endfor -%}
{%- endfor -%}
{%- endblock body -%}

{%- block footer -%}
{%- endblock footer -%}
