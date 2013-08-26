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