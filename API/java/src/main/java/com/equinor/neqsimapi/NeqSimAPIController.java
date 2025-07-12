package com.equinor.neqsimapi;

/**
 * REST controller exposing NeqSim simulations.
 *
 * <p>The controller currently exposes a single POST endpoint used by the
 * notebooks in this repository to run a TEG dehydration and regeneration
 * simulation. The heavy lifting of building the actual process model is
 * delegated to {@link com.equinor.neqsimapi.model.TEGsim}.</p>
 */
import com.equinor.neqsimapi.dto.CalcResponse;
import javax.ws.rs.Consumes;
import javax.ws.rs.POST;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;
import javax.ws.rs.QueryParam;

@Path("/ML")
public class NeqSimAPIController {

    @POST
    @Path("/dehydTEGsim")
    @Produces(MediaType.APPLICATION_JSON)
    @Consumes(MediaType.APPLICATION_JSON)
    /**
     * Execute a full dehydration and regeneration simulation.
     *
     * @param req input parameters for the process model
     * @param key optional API key, currently not validated
     * @return a {@link javax.ws.rs.core.Response} containing a {@link CalcResponse}
     *         with results or error information
     */
    public Response dehydAndRegenSimML(com.equinor.neqsimapi.dto.TEGdehydrationRequest req,
            @QueryParam("key") String key) {
        try {
            if (!req.checkValidInput()) {
                return Response.ok(new CalcResponse(new Exception("not valid input to calculation")))
                        .build();
            }
            com.equinor.neqsimapi.model.TEGsim Tegsim1 =
                    new com.equinor.neqsimapi.model.TEGsim();
            neqsim.processSimulation.processSystem.ProcessSystem operations =
                    Tegsim1.getProcess(req);
            Thread processThread = operations.runAsThread();
            try{
                processThread.join(60000 * 5);
            }
            catch(Exception e){
                return Response.ok(new CalcResponse(new Exception("calculation did not finish in maximum time")))
                        .build();
            }  
            return Response.ok(new CalcResponse(operations))
                    .build();
        } catch (Exception ex) {
            return Response.ok(new CalcResponse(ex))
                    .build();
        }
    }

    }
